# Work packet: Polymarket arrival-hazard successor replay

## Identity

- Packet: `polymarket.freeze-and-replay-arrival-hazard`.
- Parent evidence: source 03 in the stochastic-process paper study.
- Exact parent receipt SHA-256:
  `810dc73970961bc69386041973c349847b151208d8488f959aaa8e69321353b8`.
- Development source capability: expanded-corpus fresh development only.
- Replay capability: the 29 wholly later successor events only.
- Protected values are unavailable and no protected request is authorized.

## Concrete seam

Source 03 retained every fold's state and full logistic coefficients, training event count, and
move rate, but omitted the fold-fitted feature means and scales required to reconstruct a
prediction. This is a study-artifact provenance omission, not evidence against the model and not a
reason to alter the harness. The correction is a new source with new identity; source 03 remains
immutable.

## Fixed development freeze

Source 16 repeats source 03's exact data mapping, 24-increment warm-up, features, event-equal
weighting, ridge penalty `0.1`, four Newton updates, chronological folds, metrics, and gates. It
adds only two all-development fits after those comparisons:

- state: probability level, boundary distance, and winsorized logit level;
- full: the state features plus log one-plus quiet run and the prior-24 zero fraction.

For each model the receipt must retain target mean, feature indices, feature means, feature scales,
coefficients, and represented-event count. Any mismatch from source 03's existing chronological
metrics is a failed reproduction and forbids replay.

## Frozen replay

After source 16 succeeds, source 17 will contain the literal source-16 model arrays and parent
source/receipt hashes. It performs no fitting and no threshold selection on the successor cohort.
It reconstructs the same next-regular-hour binary move label and legal features after the same
24-increment warm-up.

The fixed successor gate passes only if all conditions hold:

1. full-model observation and event-macro Brier are below the frozen state model;
2. full-model observation and event-macro log loss are below the frozen state model;
3. event-macro Brier improves at least 5% relative to state;
4. the full model wins at least 60% of eligible event-level Brier comparisons;
5. full-model event-macro Brier improves in both chronological halves;
6. full-model observation and event-macro Brier are each at most `0.20`;
7. absolute mean prediction-minus-outcome calibration gap is at most `0.05`;
8. at least 20 successor events and 5,000 predictions are eligible.

These absolute gates are fixed from the earlier formal-arrival standard before the replay. Failure
is retained. Passing would support the continuous logistic arrival component on a later cohort; it
would not constitute protected validation, an executable-price model, or a trading claim.

## Budget and stopping

One development freeze source and one literal no-refit replay source are authorized. One
non-scientific correction is allowed for a syntax, invocation, or hash-transcription error that
occurs before successor values are returned. No model, feature, penalty, threshold, or population
may change in response to replay results.

## Deliverables

- exact source-16 development receipt and reproduction check against source 03;
- exact source-17 no-refit successor receipt;
- retained pass or failure with explicit epistemic status;
- paper, evidence-index, and reproducibility updates;
- local Chronos-only commit after verification.

## Completion

**COMPLETE — FROZEN SUCCESSOR GATE PASSED; PROTECTED VALUES UNEXPOSED.** Source 16 reproduced every
source-03 chronological score, fold, and gate exactly, then retained the missing all-development
means, scales, and coefficients. Source 17 embedded those literal arrays and performed no fitting
on 17,671 later predictions across 27 events. Event-macro Brier fell from `0.26106` for state to
`0.17392` for state plus staleness, a `33.38%` improvement; the full hazard won `27/27` events,
improved both chronological halves, and passed the absolute Brier and calibration gates. This is a
later no-refit replay, not protected validation or a trade claim.
