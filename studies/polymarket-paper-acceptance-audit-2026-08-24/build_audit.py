"""Build the receipt-backed Polymarket paper audit from retained campaign evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research_agent.reporting import (
    AlternativeHypothesis,
    CampaignReference,
    ClaimDeclaration,
    ClaimKind,
    EffectDirection,
    EffectInterval,
    EvidenceAssertion,
    EvidenceLocator,
    EvidenceUnit,
    HypothesisFamily,
    HypothesisTest,
    PaperAuditor,
    PaperDecision,
    PaperProtocol,
    ValueFormat,
    bootstrap_mean_interval,
    render_concise_paper,
    verify_paper_audit_json,
)

STUDY_DIRECTORY = Path(__file__).resolve().parent
CAMPAIGN_ROOT = STUDY_DIRECTORY.parent / "polymarket-enforced-research-campaign-2026-08-24"
BOOTSTRAP_REPETITIONS = 10_000


def _campaigns() -> tuple[CampaignReference, ...]:
    return (
        CampaignReference(
            "core-fresh",
            "corpus-campaign",
            "8d691987edb4eaacb3048f1ec4e8d11e6891497f441ed5a080e611b010fc5ffd",
            "231c3eed2eafa9019cba2dbfeafc73b4681667162eeb26368fc9aa99aeb432b2",
        ),
        CampaignReference(
            "core-exposed-rerun",
            "corpus-campaign-v2",
            "75cfe4363f5514ffe0ba24edacb6cd99d7922bcc10231deca50c0b55f5d961bf",
            "c969e6372c762521a0c8bd3c96dfd497bbbfe23738ae8faf1577f41461847198",
        ),
        CampaignReference(
            "behavioral-addon",
            "behavioral-addon-campaign",
            "92ce826c5ffee6e6a8e9cd7d2876204e0567062c14d75abe83a6a60fa534f964",
            "ada10620f49e65ba796d10b9d598e694db1623fc9cd1614f682da1071185b0f3",
        ),
        CampaignReference(
            "fixed-clob-exposed",
            "fixed-clob-campaign",
            "f665776d281e4558f166109570af33e2924b54699ca5724c41864a89741dd2ad",
            "43fa41e27f4f6e1feb3ff7d5e9ecd5675345627e5e39fa4b056d9bf6fa47b2ce",
        ),
        CampaignReference(
            "nonreplay-audit",
            "nonreplay-audit-campaign",
            "c269df00cb25a9414fb0c957e067bdfc00a4028174974b723198972bb4df4c7e",
            "2277a367381dd36ca772f9ad5f1962879c60088c8a80098e9c546689d85ccfc3",
        ),
    )


def _locator(campaign: str, analysis: str) -> EvidenceLocator:
    return EvidenceLocator(campaign, analysis)


def _rerun(evidence: EvidenceLocator) -> EvidenceLocator:
    return _locator("core-exposed-rerun", evidence.analysis_id)


PROCESS_INITIAL = _locator(
    "core-fresh", "stochastic.paper.event-cluster-uncertainty.initial.v1"
)
PROCESS_SUCCESSOR = _locator(
    "core-fresh", "stochastic.paper.event-cluster-uncertainty.successor.v1"
)
REPRESENTATION = _locator(
    "core-fresh", "stochastic.paper.representation-robustness.initial.v1"
)
FIVE_MINUTE = _locator(
    "fixed-clob-exposed", "stochastic.paper.five-minute-measurement-falsifier.v1"
)
ARRIVAL_REPLAY = _locator(
    "core-fresh", "stochastic.paper.frozen-arrival-replay.successor.v1"
)
PROCESS_REPLAY = _locator(
    "core-fresh", "stochastic.paper.frozen-process-replay.successor.v1"
)
REVERSAL_REPLICATION = _locator(
    "core-fresh", "stochastic.fresh-reversal.replication.v1"
)
LONGSHOT = _locator("core-fresh", "behavioral.probability-weighting.v1")
SKILLED_WALLET = _locator(
    "core-exposed-rerun", "behavioral.skilled-wallet-matched-state.v2"
)
EXPERT_CONSENSUS = _locator(
    "core-exposed-rerun", "behavioral.delayed-expert-consensus.v2"
)
ACTIVITY_MATCH = _locator(
    "behavioral-addon", "behavioral.delayed-wallet-state-activity-match.v2"
)
CROWDED = _locator(
    "behavioral-addon", "behavioral.crowded-extrapolation-exhaustion.v2"
)
FOCAL = _locator("core-fresh", "behavioral.focal-price-anchoring.v1")
AMBIGUITY = _locator("core-fresh", "behavioral.ambiguity-aversion.v1")
UNDERROUND = _locator("core-fresh", "game-theory.exhaustive-bucket-underround.v1")
BRACKET = _locator("core-fresh", "game-theory.bracket-overround-compression.v1")
NONREPLAY = _locator("nonreplay-audit", "audit.nonreplay-coverage.v1")


def _receipt(locator: EvidenceLocator) -> dict[str, object]:
    directory = next(
        reference.directory_ref
        for reference in _campaigns()
        if reference.reference_id == locator.campaign_reference_id
    )
    name = hashlib.sha256(locator.analysis_id.encode()).hexdigest()
    path = CAMPAIGN_ROOT / directory / "executions" / f"{name}.json"
    return json.loads(path.read_text())


def _details(locator: EvidenceLocator) -> dict[str, object]:
    return _receipt(locator)["details"]


def _assertion(
    evidence: EvidenceLocator,
    path: tuple[str | int, ...],
    value: str | int | float | bool,
    value_format: ValueFormat,
) -> EvidenceAssertion:
    return EvidenceAssertion(evidence, path, value, value_format)


def _process_statistics() -> tuple[
    tuple[EffectInterval, ...], tuple[HypothesisTest, ...], tuple[ClaimDeclaration, ...]
]:
    summaries = _details(PROCESS_SUCCESSOR)["summaries"]
    configurations = (
        (
            "zero-mass",
            "regular_interior_zero_rate",
            EffectDirection.ABOVE,
            "Registered hourly probabilities retained an interior zero-increment event mean of "
            "{mean} across {eligible} eligible later-cohort events, with a whole-event 95% interval "
            "from {lower} to {upper}; the fixed null was 20%.",
        ),
        (
            "sign-reversal",
            "nonzero_sign_reversal_rate",
            EffectDirection.ABOVE,
            "Adjacent nonzero changes reversed sign at an event mean of {mean} across {eligible} "
            "eligible later-cohort events, with a whole-event 95% interval from {lower} to {upper}; "
            "the fixed null was 50%.",
        ),
        (
            "quiet-duration",
            "quiet_24h_to_quiet_0_move_rate_ratio",
            EffectDirection.BELOW,
            "The long-quiet to active next-move-rate ratio had an event mean of {mean} across "
            "{eligible} eligible later-cohort events, with a whole-event 95% interval from {lower} "
            "to {upper}; the fixed null was 50%.",
        ),
        (
            "variance-scaling",
            "variance_ratio_24h",
            EffectDirection.BELOW,
            "The 24-hour variance ratio had an event mean of {mean} across {eligible} eligible "
            "later-cohort events, with a whole-event 95% interval from {lower} to {upper}; the fixed "
            "null was 75%.",
        ),
    )
    intervals = []
    tests = []
    claims = []
    common_evidence = (
        PROCESS_INITIAL,
        _rerun(PROCESS_INITIAL),
        PROCESS_SUCCESSOR,
        _rerun(PROCESS_SUCCESSOR),
        REPRESENTATION,
        _rerun(REPRESENTATION),
        FIVE_MINUTE,
    )
    for index, (short_name, key, direction, template) in enumerate(configurations, start=2):
        summary = summaries[key]
        mean = summary["event_equal_mean"]
        lower, upper = summary["fixed_event_bootstrap_mean_interval_95"]
        threshold = summary["threshold"]
        passing = summary["passing_event_count"]
        eligible = summary["eligible_event_count"]
        interval_id = f"interval:process-{short_name}"
        test_id = f"test:process-{short_name}"
        intervals.append(
            EffectInterval(
                interval_id,
                PROCESS_SUCCESSOR,
                EvidenceUnit.EVENT,
                "fixed whole-event percentile bootstrap",
                0.95,
                mean,
                lower,
                upper,
                threshold,
                direction,
                2000,
            )
        )
        tests.append(
            HypothesisTest(
                test_id,
                PROCESS_SUCCESSOR,
                "family:fixed-successor-process-signatures",
                EvidenceUnit.EVENT,
                passing,
                eligible,
                0.5,
                AlternativeHypothesis.GREATER,
            )
        )
        statement = template.format(
            mean=f"{mean:.2%}",
            eligible=eligible,
            lower=f"{lower:.2%}",
            upper=f"{upper:.2%}",
        )
        base = ("summaries", key)
        claims.append(
            ClaimDeclaration(
                f"C{index:02d}",
                statement,
                ClaimKind.PROCESS_GENERALIZATION,
                common_evidence,
                (
                    _assertion(
                        PROCESS_SUCCESSOR,
                        (*base, "eligible_event_count"),
                        eligible,
                        ValueFormat.INTEGER,
                    ),
                    _assertion(
                        PROCESS_SUCCESSOR,
                        (*base, "event_equal_mean"),
                        mean,
                        ValueFormat.PERCENT_2,
                    ),
                    _assertion(
                        PROCESS_SUCCESSOR,
                        (*base, "fixed_event_bootstrap_mean_interval_95", 0),
                        lower,
                        ValueFormat.PERCENT_2,
                    ),
                    _assertion(
                        PROCESS_SUCCESSOR,
                        (*base, "fixed_event_bootstrap_mean_interval_95", 1),
                        upper,
                        ValueFormat.PERCENT_2,
                    ),
                ),
                interval_id,
                test_id,
                (REPRESENTATION, FIVE_MINUTE),
                (PROCESS_INITIAL, PROCESS_SUCCESSOR),
                True,
                None,
                None,
                (
                    "The estimand is the registered sample process, not latent belief or price.",
                    "The later cohort is fresh development replication, not protected evidence.",
                ),
            )
        )
    return tuple(intervals), tuple(tests), tuple(claims)


def _predictive_statistics() -> tuple[
    tuple[EffectInterval, ...], tuple[HypothesisTest, ...], tuple[ClaimDeclaration, ...]
]:
    arrival = _details(ARRIVAL_REPLAY)
    arrival_model = arrival["state_plus_staleness_logistic"]
    arrival_rows = arrival_model["event_rows"]
    arrival_differences = tuple(row["comparator_brier"] - row["brier"] for row in arrival_rows)
    arrival_interval = bootstrap_mean_interval(
        arrival_differences,
        repetitions=BOOTSTRAP_REPETITIONS,
        seed=20260824,
    )
    arrival_mean = sum(arrival_differences) / len(arrival_differences)
    arrival_wins = sum(value > 0.0 for value in arrival_differences)

    reversal = _details(REVERSAL_REPLICATION)
    reversal_rows = reversal["per_event_evidence"]
    reversal_differences = tuple(row["rate_brier"] - row["state_brier"] for row in reversal_rows)
    reversal_interval = bootstrap_mean_interval(
        reversal_differences,
        repetitions=BOOTSTRAP_REPETITIONS,
        seed=20260825,
    )
    reversal_mean = sum(reversal_differences) / len(reversal_differences)
    reversal_wins = sum(value > 0.0 for value in reversal_differences)

    intervals = (
        EffectInterval(
            "interval:frozen-arrival-brier-difference",
            ARRIVAL_REPLAY,
            EvidenceUnit.EVENT,
            "whole-event percentile bootstrap of paired Brier differences",
            0.95,
            arrival_mean,
            arrival_interval[0],
            arrival_interval[1],
            0.0,
            EffectDirection.ABOVE,
            BOOTSTRAP_REPETITIONS,
        ),
        EffectInterval(
            "interval:fresh-reversal-brier-difference",
            REVERSAL_REPLICATION,
            EvidenceUnit.EVENT,
            "whole-event percentile bootstrap of paired Brier differences",
            0.95,
            reversal_mean,
            reversal_interval[0],
            reversal_interval[1],
            0.0,
            EffectDirection.ABOVE,
            BOOTSTRAP_REPETITIONS,
        ),
    )
    tests = (
        HypothesisTest(
            "test:frozen-arrival-event-wins",
            ARRIVAL_REPLAY,
            "family:stochastic-predictive-search",
            EvidenceUnit.EVENT,
            arrival_wins,
            len(arrival_differences),
            0.5,
            AlternativeHypothesis.GREATER,
        ),
        HypothesisTest(
            "test:fresh-reversal-event-wins",
            REVERSAL_REPLICATION,
            "family:stochastic-predictive-search",
            EvidenceUnit.EVENT,
            reversal_wins,
            len(reversal_differences),
            0.5,
            AlternativeHypothesis.GREATER,
        ),
    )
    arrival_improvement = arrival["event_macro_brier_relative_improvement_vs_state"]
    arrival_event_count = arrival_model["event_count"]
    reversal_event_count = reversal["state_shock_logistic"]["represented_event_count"]
    claims = (
        ClaimDeclaration(
            "C06",
            (
                "The frozen state-plus-staleness arrival model improved later-cohort event-macro "
                f"Brier by {arrival_improvement:.2%} and won {arrival_wins} of "
                f"{arrival_event_count} events; the paired event bootstrap improvement interval was "
                f"{arrival_interval[0]:.4f} to {arrival_interval[1]:.4f}."
            ),
            ClaimKind.PREDICTIVE_REPLICATION,
            (ARRIVAL_REPLAY, _rerun(ARRIVAL_REPLAY)),
            (
                _assertion(
                    ARRIVAL_REPLAY,
                    ("event_macro_brier_relative_improvement_vs_state",),
                    arrival_improvement,
                    ValueFormat.PERCENT_2,
                ),
                _assertion(
                    ARRIVAL_REPLAY,
                    ("state_plus_staleness_logistic", "event_wins_vs_comparator"),
                    arrival_wins,
                    ValueFormat.INTEGER,
                ),
                _assertion(
                    ARRIVAL_REPLAY,
                    ("state_plus_staleness_logistic", "event_count"),
                    arrival_event_count,
                    ValueFormat.INTEGER,
                ),
            ),
            "interval:frozen-arrival-brier-difference",
            "test:frozen-arrival-event-wins",
            (ARRIVAL_REPLAY,),
            (ARRIVAL_REPLAY,),
            True,
            None,
            None,
            (
                "This predicts the registered next-sample update, not a tradeable price move.",
                "The replay is fresh development evidence and is not the rejected protected run.",
            ),
        ),
        ClaimDeclaration(
            "C08",
            (
                "The fresh post-jump reversal state model improved event-macro Brier by "
                f"{reversal_mean:.4f}, won {reversal_wins} of {reversal_event_count} represented "
                f"events, and had a paired event-bootstrap interval of "
                f"{reversal_interval[0]:.4f} to {reversal_interval[1]:.4f}."
            ),
            ClaimKind.PREDICTIVE_REPLICATION,
            (REVERSAL_REPLICATION, _rerun(REVERSAL_REPLICATION)),
            (
                _assertion(
                    REVERSAL_REPLICATION,
                    ("state_shock_logistic", "event_wins_vs_comparator"),
                    reversal_wins,
                    ValueFormat.INTEGER,
                ),
                _assertion(
                    REVERSAL_REPLICATION,
                    ("state_shock_logistic", "represented_event_count"),
                    reversal_event_count,
                    ValueFormat.INTEGER,
                ),
            ),
            "interval:fresh-reversal-brier-difference",
            "test:fresh-reversal-event-wins",
            (REVERSAL_REPLICATION,),
            (REVERSAL_REPLICATION,),
            True,
            None,
            None,
            (
                "The candidate predicts reversal-first labels after sampled jumps.",
                "Its one-cent sampled-mark cost screen failed and is not execution evidence.",
            ),
        ),
    )
    return intervals, tests, claims


def _stochastic_search_evidence() -> tuple[EvidenceLocator, ...]:
    manifest = json.loads((CAMPAIGN_ROOT / "corpus-campaign" / "manifest.json").read_text())
    return tuple(
        _locator("core-fresh", analysis["analysis_id"])
        for analysis in manifest["analyses"]
        if analysis["family"] == "stochastic-process"
    )


def _other_claims() -> tuple[ClaimDeclaration, ...]:
    process_replay = _details(PROCESS_REPLAY)
    improvement = process_replay["full_event_macro_nll_relative_improvement_vs_state"]
    wins = process_replay["full_hurdle_vs_state"]["event_wins_vs_comparator"]
    events = process_replay["full_hurdle_vs_state"]["event_count"]
    longshot = _details(LONGSHOT)
    longshot_status = longshot["decisions"]["LONGSHOT_FADE"]["status"]
    skilled = _details(SKILLED_WALLET)
    expert = _details(EXPERT_CONSENSUS)
    crowded = _details(CROWDED)
    focal = _details(FOCAL)
    ambiguity = _details(AMBIGUITY)
    underround = _details(UNDERROUND)
    bracket = _details(BRACKET)
    nonreplay = _details(NONREPLAY)
    return (
        ClaimDeclaration(
            "C01",
            (
                "Every campaign execution is present, and the retained nonreplay audit inventories "
                f"{nonreplay['item_count']} governed artifacts that must not be reissued as ordinary "
                "analysis."
            ),
            ClaimKind.AUDIT_FACT,
            (NONREPLAY,),
            (
                _assertion(
                    NONREPLAY,
                    ("item_count",),
                    nonreplay["item_count"],
                    ValueFormat.INTEGER,
                ),
            ),
            None,
            None,
            (),
            (),
            False,
            None,
            None,
            ("The nonreplay audit records coverage; it does not reopen protected evidence.",),
        ),
        ClaimDeclaration(
            "C07",
            (
                "The unchanged full hurdle law improved successor event-macro NLL by "
                f"{improvement:.2%} and won {wins} of {events} events against the state-only law."
            ),
            ClaimKind.AUDIT_FACT,
            (PROCESS_REPLAY, _rerun(PROCESS_REPLAY)),
            (
                _assertion(
                    PROCESS_REPLAY,
                    ("full_event_macro_nll_relative_improvement_vs_state",),
                    improvement,
                    ValueFormat.PERCENT_2,
                ),
                _assertion(
                    PROCESS_REPLAY,
                    ("full_hurdle_vs_state", "event_wins_vs_comparator"),
                    wins,
                    ValueFormat.INTEGER,
                ),
                _assertion(
                    PROCESS_REPLAY,
                    ("full_hurdle_vs_state", "event_count"),
                    events,
                    ValueFormat.INTEGER,
                ),
            ),
            None,
            None,
            (),
            (),
            True,
            None,
            None,
            ("This is a registered-sample density result, not a trading result.",),
        ),
        ClaimDeclaration(
            "C09",
            (
                "The selection-exposed development screen recorded "
                f"`{longshot_status}` for the 2–10% longshot-fade candidate."
            ),
            ClaimKind.DEVELOPMENT_RESULT,
            (LONGSHOT, _rerun(LONGSHOT)),
            (
                _assertion(
                    LONGSHOT,
                    ("decisions", "LONGSHOT_FADE", "status"),
                    longshot_status,
                    ValueFormat.RAW,
                ),
            ),
            None,
            None,
            (LONGSHOT,),
            (LONGSHOT,),
            False,
            None,
            None,
            (
                "This is a candidate-selection result, not fresh confirmation.",
                "The two-cent hurdle is not an observed spread, fee, depth, or impact model.",
            ),
        ),
        ClaimDeclaration(
            "C10",
            (
                "The exposed behavioral reruns rejected the fixed skilled-wallet, delayed expert, "
                "activity-matched wallet, and crowded-extrapolation candidates. Skilled-wallet "
                f"incremental event-macro edge was {skilled['matched_result']['high_minus_control_event_macro_edge']:.2%}; "
                f"six-hour expert net return was {expert['six_hour']['expert_event_macro_net_return']:.2%}; "
                f"and crowded 24-hour fade return was {crowded['crowded_chase']['event_macro_fade_return_24h']:.2%}."
            ),
            ClaimKind.AUDIT_FACT,
            (SKILLED_WALLET, EXPERT_CONSENSUS, ACTIVITY_MATCH, CROWDED),
            (
                _assertion(
                    SKILLED_WALLET,
                    ("matched_result", "high_minus_control_event_macro_edge"),
                    skilled["matched_result"]["high_minus_control_event_macro_edge"],
                    ValueFormat.PERCENT_2,
                ),
                _assertion(
                    EXPERT_CONSENSUS,
                    ("six_hour", "expert_event_macro_net_return"),
                    expert["six_hour"]["expert_event_macro_net_return"],
                    ValueFormat.PERCENT_2,
                ),
                _assertion(
                    CROWDED,
                    ("crowded_chase", "event_macro_fade_return_24h"),
                    crowded["crowded_chase"]["event_macro_fade_return_24h"],
                    ValueFormat.PERCENT_2,
                ),
            ),
            None,
            None,
            (),
            (),
            False,
            None,
            None,
            (
                "These are exact exposed reproductions, not independent confirmation.",
                "Matching and delays are controls, not randomized causal identification.",
            ),
        ),
        ClaimDeclaration(
            "C11",
            (
                "The focal screen recorded "
                f"`{focal['screen_outcome']}`; ambiguity recorded "
                f"`{ambiguity['decision']}`; the underround `passes_all` result was "
                f"{underround['declared_live_quote_candidate_gate']['passes_all']}; and the bracket "
                f"discovery gate was {bracket['predeclared_discovery_gate_passed']}."
            ),
            ClaimKind.AUDIT_FACT,
            (
                FOCAL,
                _rerun(FOCAL),
                AMBIGUITY,
                _rerun(AMBIGUITY),
                UNDERROUND,
                _rerun(UNDERROUND),
                BRACKET,
                _rerun(BRACKET),
            ),
            (
                _assertion(
                    FOCAL,
                    ("screen_outcome",),
                    focal["screen_outcome"],
                    ValueFormat.RAW,
                ),
                _assertion(
                    AMBIGUITY,
                    ("decision",),
                    ambiguity["decision"],
                    ValueFormat.RAW,
                ),
                _assertion(
                    UNDERROUND,
                    ("declared_live_quote_candidate_gate", "passes_all"),
                    underround["declared_live_quote_candidate_gate"]["passes_all"],
                    ValueFormat.RAW,
                ),
                _assertion(
                    BRACKET,
                    ("predeclared_discovery_gate_passed",),
                    bracket["predeclared_discovery_gate_passed"],
                    ValueFormat.RAW,
                ),
            ),
            None,
            None,
            (),
            (),
            False,
            None,
            None,
            ("Disposition and NegRisk mechanisms remain blocked by missing historical state.",),
        ),
        ClaimDeclaration(
            "C12",
            (
                "The verified campaigns contain no execution-validated strategy; a profitability "
                "claim requires historical quotes or order books, observed spreads and fees, "
                "latency, queue position, partial fills, and event-level net-edge uncertainty."
            ),
            ClaimKind.EVIDENCE_BOUNDARY,
            (
                NONREPLAY,
                LONGSHOT,
                _rerun(LONGSHOT),
                REVERSAL_REPLICATION,
                _rerun(REVERSAL_REPLICATION),
            ),
            (),
            None,
            None,
            (),
            (),
            False,
            None,
            None,
            ("Sampled probabilities and fixed cost haircuts are not executable evidence.",),
        ),
        ClaimDeclaration(
            "C13",
            (
                "The longshot-fade candidate is not confirmed; confirmation requires a frozen "
                "one-shot evaluation on a new untouched chronological cohort."
            ),
            ClaimKind.EVIDENCE_BOUNDARY,
            (LONGSHOT, _rerun(LONGSHOT), NONREPLAY),
            (),
            None,
            None,
            (),
            (),
            False,
            None,
            None,
            ("Reusing the exposed development cohort cannot restore freshness.",),
        ),
    )


def build_protocol() -> PaperProtocol:
    process_intervals, process_tests, process_claims = _process_statistics()
    predictive_intervals, predictive_tests, predictive_claims = _predictive_statistics()
    families = (
        HypothesisFamily(
            "family:fixed-successor-process-signatures",
            tuple(test.test_id for test in process_tests),
            (PROCESS_SUCCESSOR,),
            True,
        ),
        HypothesisFamily(
            "family:stochastic-predictive-search",
            tuple(test.test_id for test in predictive_tests),
            _stochastic_search_evidence(),
            False,
        ),
    )
    claims = tuple(
        sorted(
            (*process_claims, *predictive_claims, *_other_claims()),
            key=lambda claim: claim.claim_id,
        )
    )
    return PaperProtocol.create(
        title="What survived rigorous behavioral and stochastic testing on Polymarket?",
        campaigns=_campaigns(),
        claims=claims,
        intervals=(*process_intervals, *predictive_intervals),
        tests=(*process_tests, *predictive_tests),
        families=families,
        alpha=0.05,
    )


def _publish_exact(path: Path, content: str) -> None:
    encoded = content.encode()
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError(f"immutable output conflicts with {path}")
        return
    path.write_bytes(encoded)


def main() -> None:
    protocol = build_protocol()
    report = PaperAuditor(root=CAMPAIGN_ROOT).audit(protocol)
    if report.decision is not PaperDecision.ACCEPT:
        failures = [claim.claim_id for claim in report.claims if not claim.passed]
        raise RuntimeError(f"paper acceptance rejected claims: {failures}")
    serialized_report = report.to_json() + "\n"
    verify_paper_audit_json(serialized_report)
    _publish_exact(STUDY_DIRECTORY / "paper-protocol.json", protocol.to_json() + "\n")
    _publish_exact(STUDY_DIRECTORY / "paper-acceptance-receipt.json", serialized_report)
    _publish_exact(STUDY_DIRECTORY / "PAPER.md", render_concise_paper(report))
    print(report.report_id)


if __name__ == "__main__":
    main()
