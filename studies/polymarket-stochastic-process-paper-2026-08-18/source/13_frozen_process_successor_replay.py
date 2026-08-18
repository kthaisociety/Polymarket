markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")

MEASUREMENT_HALF_WIDTH = 0.0005
PARENT_SOURCE_SHA256 = "13ea0c25a8e65da52cad44f4fa70a863790760cb9f2d67774769744cefbb477b"
PARENT_RECEIPT_SHA256 = "2c107a29710e3dd9d13cbf24be00e655b4b0a5c3a628fd8026670a1ad88cd9c5"
FROZEN_MODEL = [
    152,
    0.3510821749729082,
    0.44980541354883685,
    -5.511608966206509,
    1.5177775004973364,
    0.006024198774813598,
    [0.21051844080463564, 0.33417625515954963, 0.2562740198155405, 0.18516884837563216, 0.42176574765709124, 0.5342951292287202, 0.5169104782947631, 0.3767091213083616, 0.4987558662406714, 0.5188593286355139, 0.3846878012644065, 0.47121484108085054, 0.3750397144271792, 0.3559279921447089, 0.3447649229300709, 0.3666586716187143, 0.34262999062538346, 0.3516221280933754, 0.3521631550110888, 0.3466970472635364],
    [0.49831668654870187, 0.23199656653427417, 0.10097327352518275, 0.05079189038667774, 0.6645450116686462, 0.3266333753001035, 0.13634160306401955, 0.09495624981792031, 0.6796333449269373, 0.35627159608396985, 0.17294725021277416, 0.17993396369096346, 0.5261646316096484, 0.36407288966765017, 0.24268658443149468, 0.23795028228276868, 0.36555427369495214, 0.33959884366614307, 0.34210511183158754, 0.3449347552417092],
    [0.42493934001682077, 0.2822212757480613, 0.4793406269585841, 0.4493302736167706, 0.3564845963056578, 0.5259766060510821, 0.42662016984534423, 0.4556973341794484, 0.4450076813592832, 0.40337746650004286, 0.4819663470880247, 0.44784880983728437, 0.48196935970968247, 0.4592588122085683, 0.446366048556051, 0.47636168629064907, 0.48420572985061777, 0.44728349750297824, 0.45260209122919354, 0.46088380214246577],
    [0.5414380316517716, 0.44882689299445466, 0.2936189359586582, 0.5279138498684138, 0.4426497907299932, 0.3586734734539978, 0.5293095969635032, 0.4467207785448377, 0.3656436950215192, 0.5913390046458807, 0.45175463527215975, 0.3675388414706956, 0.4822865624975993, 0.44985207975633906, 0.4614514755894093],
    [[-5.942625387621129, 1.4441499176792583], [-6.6297465704246985, 1.3776174245005812], [-6.524909961026339, 1.0828802324453166], [-6.830159632286408, 0.9648291991830515], [-5.333465903597532, 1.547827729254926], [-5.109968038029732, 1.4351656816831002], [-5.4336578327081355, 1.4479204766037173], [-5.615022651192778, 1.3030707668913006], [-4.666372656199688, 1.6883100899629986], [-4.730383194628326, 1.3091583562284832], [-4.287595869493101, 1.3535490224256304], [-4.278191831940459, 1.1128914578577824], [-5.339899465290988, 1.566253242308826], [-5.5262313777232235, 1.50994196709461], [-5.476657305696488, 1.5411180413001246], [-5.732222551318178, 1.2905518336998405], [-5.5634742106261, 1.4995193462423175], [-5.513459075387636, 1.5159048411022802], [-5.575772374681886, 1.520776343098992], [-5.771063463517591, 1.4986165117077168]],
    [[-5.580694952449166, 1.5143641664353473], [-6.872750103630883, 0.915474981989329], [-5.930860070573764, 1.301044097655268], [-5.60534968886112, 1.5309421590204124], [-5.541440356366314, 1.5096940565402537], [-5.476593467149121, 1.524922047491591], [-6.238530434695934, 1.1951204585350255], [-5.0039363470135205, 1.0074124994507305], [-4.6093952036899495, 1.328874198403094], [-4.793448640949276, 1.7142873440330615], [-5.484817231616475, 1.5317547635670783], [-5.13042705348352, 1.4885135583936462], [-4.441041636674226, 1.0140347252960304], [-4.016150773933556, 1.1729247202931177], [-4.066955318874586, 1.7098123875034428], [-5.508809004641766, 1.5158819387374658], [-6.149305052735931, 1.3389840721560113], [-5.261606009218957, 1.1566085678384297], [-5.304287781160796, 1.5520201925981756], [-5.405175181949173, 1.5716042692469057], [-5.511599811746458, 1.517713457456817], [-5.827483384399762, 1.4894849239670735], [-5.550025115663559, 1.5181897750165356], [-5.504269626037003, 1.5100202764243653], [-5.5088655605068615, 1.5061572233385803]],
    [0.0026677955561469546, 0.003250057813411018, 0.0010890367156174453, 0.004994469794554983, 0.08816249880035222, 0.005398508934408048, 0.013672681428475286, 0.0035271679436408064, 0.015849709431839467, 0.0049585616162726946, 0.007158116327910631, 0.0059702088128059235, 0.019733587241545853, 0.005913202390520172, 0.00703595032017083, 0.005299504438039287, 0.005519202752863804, 0.006010916286243504, 0.0059629316095419485, 0.005341204176888925],
]


def clipped_probability(value):
    return min(0.999999999999, max(0.000000000001, value))


def probability_band(value):
    if value <= 0.02:
        return 0
    if value < 0.20:
        return 1
    if value <= 0.80:
        return 2
    if value < 0.98:
        return 3
    return 4


def close_band(hours):
    if hours <= 24.0:
        return 0
    if hours <= 72.0:
        return 1
    if hours <= 168.0:
        return 2
    return 3


def quiet_band(quiet_run):
    if quiet_run == 0:
        return 0
    if quiet_run <= 5:
        return 1
    if quiet_run <= 23:
        return 2
    return 3


def magnitude_band(magnitude):
    if magnitude == 0.0:
        return 0
    if magnitude <= 0.005:
        return 1
    if magnitude <= 0.02:
        return 2
    if magnitude <= 0.10:
        return 3
    return 4


def normal_cdf(value):
    absolute = abs(value)
    tail = 1.0 / (1.0 + 0.2316419 * absolute)
    density = 0.3989422804014327 * exp(-0.5 * absolute * absolute)
    polynomial = tail * (
        0.319381530
        + tail
        * (-0.356563782 + tail * (1.781477937 + tail * (-1.821255978 + tail * 1.330274429)))
    )
    result = 1.0 - density * polynomial
    if value < 0.0:
        result = 1.0 - result
    return min(1.0, max(0.0, result))


def normal_interval_probability(value, mean, scale):
    bounded_scale = max(0.000001, scale)
    upper = normal_cdf((value + MEASUREMENT_HALF_WIDTH - mean) / bounded_scale)
    lower = normal_cdf((value - MEASUREMENT_HALF_WIDTH - mean) / bounded_scale)
    return clipped_probability(upper - lower)


def lognormal_interval_probability(magnitude, mean, scale):
    lower_value = max(0.000001, magnitude - MEASUREMENT_HALF_WIDTH)
    upper_value = min(1.0, magnitude + MEASUREMENT_HALF_WIDTH)
    bounded_scale = max(0.05, scale)
    upper = normal_cdf((log(upper_value) - mean) / bounded_scale)
    lower = normal_cdf((log(lower_value) - mean) / bounded_scale)
    return clipped_probability(upper - lower)


def hurdle_probability(family, row):
    state = probability_bands[row] * 4 + close_bands[row]
    if family == "constant":
        move_probability = FROZEN_MODEL[1]
        positive_probability = FROZEN_MODEL[2]
        magnitude_parameters = [FROZEN_MODEL[3], FROZEN_MODEL[4]]
    elif family == "state":
        move_probability = FROZEN_MODEL[6][state]
        positive_probability = FROZEN_MODEL[8][state]
        magnitude_parameters = FROZEN_MODEL[10][state]
    else:
        arrival_cell = probability_bands[row] * 4 + quiet_bands[row]
        sign_cell = probability_bands[row] * 3 + prior_sign_bands[row]
        magnitude_cell = probability_bands[row] * 5 + prior_magnitude_bands[row]
        move_probability = FROZEN_MODEL[7][arrival_cell]
        positive_probability = FROZEN_MODEL[9][sign_cell]
        magnitude_parameters = FROZEN_MODEL[11][magnitude_cell]
    if move_labels[row] == 0:
        return clipped_probability(1.0 - move_probability)
    sign_probability = positive_probability
    if positive_labels[row] == 0:
        sign_probability = 1.0 - positive_probability
    return clipped_probability(
        move_probability
        * sign_probability
        * lognormal_interval_probability(
            abs(changes[row]), magnitude_parameters[0], magnitude_parameters[1]
        )
    )


def diffusion_probability(row):
    state = probability_bands[row] * 4 + close_bands[row]
    shape = max(0.001, probability_levels[row] * (1.0 - probability_levels[row]))
    scale = (max(0.000000000001, FROZEN_MODEL[12][state]) * shape) ** 0.5
    return normal_interval_probability(changes[row], 0.0, scale)


def summarize(losses, comparator_losses):
    slots = max(row_events) + 1
    counts = [0 for unused in range(slots)]
    totals = [0.0 for unused in range(slots)]
    comparators = [0.0 for unused in range(slots)]
    observation_total = 0.0
    event_values = []
    wins = 0
    for row in range(sample_count):
        event = row_events[row]
        counts[event] = counts[event] + 1
        totals[event] = totals[event] + losses[row]
        comparators[event] = comparators[event] + comparator_losses[row]
        observation_total = observation_total + losses[row]
    for event in range(slots):
        if counts[event] > 0:
            value = totals[event] / counts[event]
            comparator = comparators[event] / counts[event]
            if value < comparator:
                wins = wins + 1
            event_values = event_values + [value]
    midpoint = len(event_values) // 2
    return {
        "prediction_count": sample_count,
        "event_count": len(event_values),
        "observation_mean_nll": observation_total / sample_count,
        "event_macro_mean_nll": sum(event_values) / len(event_values),
        "early_event_macro_mean_nll": sum(event_values[:midpoint]) / midpoint,
        "late_event_macro_mean_nll": sum(event_values[midpoint:])
        / (len(event_values) - midpoint),
        "event_wins_vs_comparator": wins,
    }


close_by_market = {}
for row in range(len(outcome_markets)):
    close_by_market[outcome_markets[row]] = close_times[row]

maximum_rows = len(probabilities)
row_events = [0 for unused in range(maximum_rows)]
changes = [0.0 for unused in range(maximum_rows)]
probability_levels = [0.0 for unused in range(maximum_rows)]
probability_bands = [0 for unused in range(maximum_rows)]
close_bands = [0 for unused in range(maximum_rows)]
quiet_bands = [0 for unused in range(maximum_rows)]
prior_sign_bands = [1 for unused in range(maximum_rows)]
prior_magnitude_bands = [0 for unused in range(maximum_rows)]
move_labels = [0 for unused in range(maximum_rows)]
positive_labels = [0 for unused in range(maximum_rows)]
sample_count = 0
order_break_count = 0
current_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
previous_nonzero_sign = 0
previous_nonzero_magnitude = 0.0
quiet_run = 0
recent_changes = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        current_market = market
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        previous_nonzero_sign = 0
        previous_nonzero_magnitude = 0.0
        quiet_run = 0
        recent_changes = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    if previous_time is not None:
        if ordinal != previous_ordinal + 1 or observed_time <= previous_time:
            order_break_count = order_break_count + 1
            previous_nonzero_sign = 0
            previous_nonzero_magnitude = 0.0
            quiet_run = 0
            recent_changes = []
        else:
            gap_hours = (observed_time - previous_time) / 3600.0
            if gap_hours < 0.75 or gap_hours > 1.25:
                previous_nonzero_sign = 0
                previous_nonzero_magnitude = 0.0
                quiet_run = 0
                recent_changes = []
            else:
                change = probability - previous_probability
                hours_to_close = (close_by_market[market] - previous_time) / 3600.0
                if len(recent_changes) == 24 and hours_to_close >= 0.0:
                    row_events[sample_count] = event
                    changes[sample_count] = change
                    probability_levels[sample_count] = previous_probability
                    probability_bands[sample_count] = probability_band(previous_probability)
                    close_bands[sample_count] = close_band(hours_to_close)
                    quiet_bands[sample_count] = quiet_band(quiet_run)
                    prior_sign_bands[sample_count] = previous_nonzero_sign + 1
                    prior_magnitude_bands[sample_count] = magnitude_band(
                        previous_nonzero_magnitude
                    )
                    if change != 0.0:
                        move_labels[sample_count] = 1
                        if change > 0.0:
                            positive_labels[sample_count] = 1
                    sample_count = sample_count + 1
                recent_changes = recent_changes + [change]
                if len(recent_changes) > 24:
                    recent_changes = recent_changes[1:]
                if change == 0.0:
                    quiet_run = quiet_run + 1
                else:
                    quiet_run = 0
                    previous_nonzero_magnitude = abs(change)
                    previous_nonzero_sign = 1
                    if change < 0.0:
                        previous_nonzero_sign = -1
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

row_events = row_events[:sample_count]
changes = changes[:sample_count]
probability_levels = probability_levels[:sample_count]
probability_bands = probability_bands[:sample_count]
close_bands = close_bands[:sample_count]
quiet_bands = quiet_bands[:sample_count]
prior_sign_bands = prior_sign_bands[:sample_count]
prior_magnitude_bands = prior_magnitude_bands[:sample_count]
move_labels = move_labels[:sample_count]
positive_labels = positive_labels[:sample_count]

diffusion_losses = [0.0 for unused in range(sample_count)]
constant_losses = [0.0 for unused in range(sample_count)]
state_losses = [0.0 for unused in range(sample_count)]
full_losses = [0.0 for unused in range(sample_count)]
for row in range(sample_count):
    diffusion_losses[row] = -log(diffusion_probability(row))
    constant_losses[row] = -log(hurdle_probability("constant", row))
    state_losses[row] = -log(hurdle_probability("state", row))
    full_losses[row] = -log(hurdle_probability("full", row))

diffusion_metrics = summarize(diffusion_losses, diffusion_losses)
constant_metrics = summarize(constant_losses, diffusion_losses)
state_metrics = summarize(state_losses, constant_losses)
full_vs_state = summarize(full_losses, state_losses)
full_vs_diffusion = summarize(full_losses, diffusion_losses)
relative_improvement = (
    state_metrics["event_macro_mean_nll"] - full_vs_state["event_macro_mean_nll"]
) / state_metrics["event_macro_mean_nll"]
replication_gate = (
    full_vs_state["observation_mean_nll"] < state_metrics["observation_mean_nll"]
    and full_vs_state["event_macro_mean_nll"] < state_metrics["event_macro_mean_nll"]
    and full_vs_diffusion["observation_mean_nll"] < diffusion_metrics["observation_mean_nll"]
    and full_vs_diffusion["event_macro_mean_nll"] < diffusion_metrics["event_macro_mean_nll"]
    and relative_improvement >= 0.02
    and full_vs_state["event_wins_vs_comparator"] / full_vs_state["event_count"] >= 0.60
    and full_vs_diffusion["event_wins_vs_comparator"] / full_vs_diffusion["event_count"] >= 0.60
    and full_vs_state["early_event_macro_mean_nll"]
    < state_metrics["early_event_macro_mean_nll"]
    and full_vs_state["late_event_macro_mean_nll"]
    < state_metrics["late_event_macro_mean_nll"]
    and full_vs_diffusion["early_event_macro_mean_nll"]
    < diffusion_metrics["early_event_macro_mean_nll"]
    and full_vs_diffusion["late_event_macro_mean_nll"]
    < diffusion_metrics["late_event_macro_mean_nll"]
)

result = structured_return(
    "Frozen composed process law on wholly later successor events.",
    {
        "schema_version": "polymarket-frozen-process-successor-replay/v1",
        "parent_source_sha256": PARENT_SOURCE_SHA256,
        "parent_receipt_sha256": PARENT_RECEIPT_SHA256,
        "frozen_training_event_count": FROZEN_MODEL[0],
        "measurement_half_width_probability": MEASUREMENT_HALF_WIDTH,
        "warmup_regular_increment_count": 24,
        "sample_count": sample_count,
        "event_count": max(row_events) + 1,
        "coverage_checks": {"order_break_count": order_break_count},
        "bounded_diffusion": diffusion_metrics,
        "memoryless_hurdle": constant_metrics,
        "state_hurdle": state_metrics,
        "full_hurdle_vs_state": full_vs_state,
        "full_hurdle_vs_diffusion": full_vs_diffusion,
        "full_event_macro_nll_relative_improvement_vs_state": relative_improvement,
        "frozen_successor_replication_gate_passed": replication_gate,
        "protected_values_exposed": False,
    },
    warnings=[
        "Every parameter was frozen from the earlier 157-event development cohort before successor values were read.",
        "No coefficient, cell, prior, interval width, threshold, or gate is refitted on successor events.",
        "Scores use the same fixed 0.001-wide observation intervals as the parent comparison.",
        "These are sampled probabilities, not trades, quotes, latent beliefs, or executable returns.",
        "The replay is fresh development replication, not protected evaluation or scientific promotion.",
        "Ancestor and final protected values remain unavailable.",
    ],
)
