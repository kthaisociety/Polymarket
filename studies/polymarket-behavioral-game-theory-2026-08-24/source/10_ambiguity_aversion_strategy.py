"""Test a fixed question-complexity proxy for ambiguity-aversion underpricing."""

markets = read("polymarket-development-prices", "market_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read(
    "polymarket-development-outcomes", "event_chronological_ordinal"
)
questions = read("polymarket-development-outcomes", "question")
outcome_labels = read("polymarket-development-outcomes", "outcome_label")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
payouts = read("polymarket-development-outcomes", "resolution_payout")

horizon_hours = 168.0
horizon_tolerance = 24.0
minimum_probability = 0.20
maximum_probability = 0.80
adverse_execution_hurdle = 0.02
minimum_incremental_edge = 0.01
event_count = max(outcome_events) + 1
price_band_count = 20


def contains_any(text, variants):
    for variant in variants:
        if variant in text:
            return True
    return False


conditional_variants = [
    " if ",
    " If ",
    " IF ",
    " unless ",
    " Unless ",
    " UNLESS ",
    " in case ",
    " In case ",
    " IN CASE ",
]
alternative_variants = [
    " or ",
    " Or ",
    " OR ",
    " either ",
    " Either ",
    " EITHER ",
]
boundary_variants = [
    " at least ",
    " At least ",
    " AT LEAST ",
    " more than ",
    " More than ",
    " MORE THAN ",
    " less than ",
    " Less than ",
    " LESS THAN ",
    " between ",
    " Between ",
    " BETWEEN ",
    " before ",
    " Before ",
    " BEFORE ",
    " by ",
    " By ",
    " BY ",
]


def ambiguity_score(question):
    score = 0
    if len(question) >= 80:
        score = score + 1
    if contains_any(question, conditional_variants):
        score = score + 1
    if contains_any(question, alternative_variants):
        score = score + 1
    if contains_any(question, boundary_variants):
        score = score + 1
    return score


event_by_market = {}
close_by_market = {}
payout_by_market = {}
question_by_market = {}
score_by_market = {}
best_distance_by_market = {}
best_probability_by_market = {}
score_counts = [0, 0, 0, 0, 0]
label_counts = {}
category_counts = {
    "length_ge_80": 0,
    "conditional": 0,
    "alternative": 0,
    "boundary": 0,
}

for row in range(len(outcome_markets)):
    market = outcome_markets[row]
    question = questions[row]
    score = ambiguity_score(question)
    event_by_market[market] = outcome_events[row]
    close_by_market[market] = close_times[row]
    payout_by_market[market] = payouts[row]
    question_by_market[market] = question
    score_by_market[market] = score
    best_distance_by_market[market] = None
    best_probability_by_market[market] = None
    score_counts[score] = score_counts[score] + 1
    if len(question) >= 80:
        category_counts["length_ge_80"] = category_counts["length_ge_80"] + 1
    if contains_any(question, conditional_variants):
        category_counts["conditional"] = category_counts["conditional"] + 1
    if contains_any(question, alternative_variants):
        category_counts["alternative"] = category_counts["alternative"] + 1
    if contains_any(question, boundary_variants):
        category_counts["boundary"] = category_counts["boundary"] + 1
    label = outcome_labels[row]
    if label not in label_counts:
        label_counts[label] = 0
    label_counts[label] = label_counts[label] + 1

order_break_count = 0
current_market = None
previous_ordinal = None
previous_time = None
for row in range(len(probabilities)):
    market = markets[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        current_market = market
        previous_ordinal = None
        previous_time = None
        if ordinal != 0:
            order_break_count = order_break_count + 1
    elif ordinal != previous_ordinal + 1 or observed_time <= previous_time:
        order_break_count = order_break_count + 1
    hours_to_close = (close_by_market[market] - observed_time) / 3600.0
    distance = abs(hours_to_close - horizon_hours)
    best_distance = best_distance_by_market[market]
    if (
        hours_to_close >= 0.0
        and distance <= horizon_tolerance
        and (best_distance is None or distance < best_distance)
    ):
        best_distance_by_market[market] = distance
        best_probability_by_market[market] = probability
    previous_ordinal = ordinal
    previous_time = observed_time


def cohort_index(score):
    if score >= 2:
        return 0
    if score == 0:
        return 1
    return None


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


cohort_names = ["COMPLEX", "SIMPLE"]
market_counts = [0, 0]
event_signal_counts = [[0 for event in range(event_count)] for cohort in range(2)]
event_edge_sums = [[0.0 for event in range(event_count)] for cohort in range(2)]
cell_signal_counts = [
    [[0 for band in range(price_band_count)] for event in range(event_count)]
    for cohort in range(2)
]
cell_edge_sums = [
    [[0.0 for band in range(price_band_count)] for event in range(event_count)]
    for cohort in range(2)
]
eligible_intermediate_count = 0
missing_horizon_count = 0
outside_probability_count = 0

for market in outcome_markets:
    probability = best_probability_by_market[market]
    if probability is None:
        missing_horizon_count = missing_horizon_count + 1
        continue
    if probability < minimum_probability or probability > maximum_probability:
        outside_probability_count = outside_probability_count + 1
        continue
    cohort = cohort_index(score_by_market[market])
    if cohort is None:
        eligible_intermediate_count = eligible_intermediate_count + 1
        continue
    event = event_by_market[market]
    edge = payout_by_market[market] - probability - adverse_execution_hurdle
    band = int(probability * 20.0)
    if band >= price_band_count:
        band = price_band_count - 1
    market_counts[cohort] = market_counts[cohort] + 1
    event_signal_counts[cohort][event] = event_signal_counts[cohort][event] + 1
    event_edge_sums[cohort][event] = event_edge_sums[cohort][event] + edge
    cell_signal_counts[cohort][event][band] = (
        cell_signal_counts[cohort][event][band] + 1
    )
    cell_edge_sums[cohort][event][band] = (
        cell_edge_sums[cohort][event][band] + edge
    )

cohort_rows = []
cohort_metrics = [None, None]
for cohort in range(2):
    event_edges = []
    early_edges = []
    late_edges = []
    positive_event_count = 0
    for event in range(event_count):
        count = event_signal_counts[cohort][event]
        if count > 0:
            edge = event_edge_sums[cohort][event] / count
            event_edges = event_edges + [edge]
            if edge > 0.0:
                positive_event_count = positive_event_count + 1
            if event < event_count // 2:
                early_edges = early_edges + [edge]
            else:
                late_edges = late_edges + [edge]
    metrics = {
        "cohort": cohort_names[cohort],
        "market_count": market_counts[cohort],
        "event_count": len(event_edges),
        "event_macro_net_edge": safe_rate(sum(event_edges), len(event_edges)),
        "early_event_macro_net_edge": safe_rate(sum(early_edges), len(early_edges)),
        "late_event_macro_net_edge": safe_rate(sum(late_edges), len(late_edges)),
        "positive_event_share": safe_rate(positive_event_count, len(event_edges)),
    }
    cohort_metrics[cohort] = metrics
    cohort_rows = cohort_rows + [metrics]

paired_event_differences = []
early_paired_differences = []
late_paired_differences = []
paired_cell_count = 0
for event in range(event_count):
    event_differences = []
    for band in range(price_band_count):
        complex_count = cell_signal_counts[0][event][band]
        simple_count = cell_signal_counts[1][event][band]
        if complex_count > 0 and simple_count > 0:
            complex_edge = cell_edge_sums[0][event][band] / complex_count
            simple_edge = cell_edge_sums[1][event][band] / simple_count
            event_differences = event_differences + [complex_edge - simple_edge]
            paired_cell_count = paired_cell_count + 1
    if len(event_differences) > 0:
        event_difference = sum(event_differences) / len(event_differences)
        paired_event_differences = paired_event_differences + [event_difference]
        if event < event_count // 2:
            early_paired_differences = early_paired_differences + [event_difference]
        else:
            late_paired_differences = late_paired_differences + [event_difference]

paired_result = {
    "paired_event_count": len(paired_event_differences),
    "paired_cell_count": paired_cell_count,
    "complex_minus_simple_event_macro_net_edge": safe_rate(
        sum(paired_event_differences), len(paired_event_differences)
    ),
    "early_complex_minus_simple_net_edge": safe_rate(
        sum(early_paired_differences), len(early_paired_differences)
    ),
    "late_complex_minus_simple_net_edge": safe_rate(
        sum(late_paired_differences), len(late_paired_differences)
    ),
}

complex_row = cohort_metrics[0]
coverage_passed = complex_row["market_count"] >= 100 and complex_row["event_count"] >= 30
chronology_passed = (
    complex_row["early_event_macro_net_edge"] is not None
    and complex_row["late_event_macro_net_edge"] is not None
    and complex_row["early_event_macro_net_edge"] > 0.0
    and complex_row["late_event_macro_net_edge"] > 0.0
)
paired_coverage_passed = (
    paired_result["paired_event_count"] >= 20
    and paired_result["paired_cell_count"] >= 40
)
paired_increment_passed = (
    paired_result["complex_minus_simple_event_macro_net_edge"] is not None
    and paired_result["early_complex_minus_simple_net_edge"] is not None
    and paired_result["late_complex_minus_simple_net_edge"] is not None
    and paired_result["complex_minus_simple_event_macro_net_edge"]
    >= minimum_incremental_edge
    and paired_result["early_complex_minus_simple_net_edge"] >= 0.0
    and paired_result["late_complex_minus_simple_net_edge"] >= 0.0
)
passed = (
    coverage_passed
    and chronology_passed
    and paired_coverage_passed
    and paired_increment_passed
)

result = structured_return(
    "Fixed ambiguity-aversion strategy screen against simple wording in matched event/probability cells.",
    {
        "schema_version": "polymarket-ambiguity-aversion/v1",
        "horizon_hours": horizon_hours,
        "horizon_tolerance_hours": horizon_tolerance,
        "probability_scope": "[0.20,0.80]",
        "adverse_execution_hurdle": adverse_execution_hurdle,
        "minimum_incremental_edge": minimum_incremental_edge,
        "proxy": {
            "complex_minimum_score": 2,
            "simple_score": 0,
            "score_counts_all_development_markets": score_counts,
            "category_counts_all_development_markets": category_counts,
        },
        "label_counts": label_counts,
        "order_break_count": order_break_count,
        "missing_horizon_count": missing_horizon_count,
        "outside_probability_count": outside_probability_count,
        "eligible_intermediate_score_count": eligible_intermediate_count,
        "cohort_rows": cohort_rows,
        "paired_result": paired_result,
        "decision_checks": {
            "coverage_passed": coverage_passed,
            "chronology_passed": chronology_passed,
            "paired_coverage_passed": paired_coverage_passed,
            "paired_increment_passed": paired_increment_passed,
        },
        "decision": (
            "RETAIN_FOR_FRESH_REPLICATION"
            if passed
            else "REJECT_FIXED_AMBIGUITY_PROXY_CANDIDATE"
        ),
    },
    warnings=[
        "The whole-event development partition is selection-exposed; protected values remain hidden.",
        "Question wording is a fixed observable proxy, not proof of subjective ambiguity or causal aversion.",
        "Descriptions and resolution rules are absent and were not inferred from question text.",
        "Sampled probabilities are not executable bid or ask quotes.",
        "Each market contributes at most one sample at the fixed horizon.",
        "The two-cent hurdle is a stress screen, not an observed spread, fee, depth, or impact model.",
        "Passing permits only fresh immutable replication, never promotion or trading.",
    ],
)
