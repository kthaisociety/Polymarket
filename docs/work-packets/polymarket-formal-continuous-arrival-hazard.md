# Work packet: Formal continuous Polymarket arrival hazard

## Identity and ancestry

- Packet: `polymarket.formalize-continuous-arrival-hazard`.
- Positive parent: source 16 exact development freeze and source 17 frozen later replay.
- Negative parent: source 14 coarse-cell formal development rejection.
- Trial status: explicitly descended, selection-exposed development; not a repair of source 14.
- Protected status: original final 47 events remain unavailable.

## Exact question

Can the continuous logistic hazard that succeeded in chronological development and a no-refit
later replay meet the existing formal binary-arrival credibility standard on source 14's exact
metadata-fixed sparse decision schedule?

The target remains whether the next registered sample, 45–75 minutes after the decision, changes.
It is not direction, resolution, latent belief, a quote, or an executable return.

## Fixed candidate

The authored candidate uses the exact source-03/source-16 feature semantics:

1. current probability level;
2. distance to the nearest boundary;
3. logit probability winsorized only for the transform at `[0.005, 0.995]`;
4. `log(1 + quiet run)` over consecutive legal regular-hour increments;
5. fraction of exact-zero changes in the prior 24 regular increments.

The candidate requires 25 consecutive regular observations. Irregular history is excluded through
the declared missingness policy. Inside each temporal fold it fits feature means, feature scales,
and a logistic model with event-equal row weights, ridge penalty `0.1`, and exactly four Newton
updates. Prediction is inference-only.

No feature, transform, penalty, iteration count, sampling key, label, metric, or threshold may
change after execution.

## Development population and gates

Use source 14's exact expanded-corpus fresh-development partition, metadata-selected common anchors,
up to five markets per anchor, last-25-history projection, next-75-minute outcome window, expanding
temporal evaluation, minimum 100 training rows, and 200 OOF-row feasibility minimum. Because the
authored interface requires exact feature outputs rather than a `None` missingness signal, retain
only source-14 keys whose last 25 observations form 24 regular gaps; do not replace a dropped key or
choose a new anchor. This is the schedule-side implementation of the predeclared source-03 warm-up.

The fixed credibility gate is unchanged from source 14:

- at least 200 OOF predictions and 80 events;
- observation MSE/Brier at most `0.20`;
- event-macro MSE/Brier at most `0.20`;
- early and late event-macro MSE/Brier each at most `0.22`;
- absolute mean prediction-minus-outcome gap at most `0.05`;
- largest event share of squared error at most `0.10`.

Failure is retained as a formal development rejection. Passing permits an independent service to
seal this exact candidate but does not expose protected values.

## Predeclared protected plan

The protected scenario, exact final-47-event decision schedule, expanding training protocol,
missingness policy, MSE/MAE/coverage/failure metrics, stability/concentration views, and absolute
promotion criteria are constructed before development outcomes are interpreted. The claim is
limited to the exact continuous hazard and registered sampled-move target.

Even after a development pass, a separate gate audit must verify frozen identity, trial ancestry,
coverage, failures, and authority separation before any protected request. The researcher cannot
approve its own request.

## Budget and stopping

One formal candidate is authorized. One correction is allowed only for an execution defect visible
before scientific metrics are returned. A scientific failure ends this branch. Thresholds and the
decision schedule cannot be relaxed.

## Deliverables

- exact formal driver and immutable receipt;
- candidate/evidence/freeze identities or explicit rejection;
- protected-exposure status;
- paper and evidence-index update;
- verified local Chronos-only commit.

## Completion

**COMPLETE — FORMAL DEVELOPMENT GATE PASSED; CANDIDATE FROZEN; PROTECTED VALUES UNEXPOSED.** The
first execution returned no candidate evidence because `make_features()` cannot use `None` as a
missingness signal. Before any metric was returned, the one permitted execution correction moved
the already declared 25-regular-observation rule into a metadata-only key filter; dropped source-14
keys were not replaced. The final run produced 202 OOF predictions across 100 events. Observation
Brier was `0.18256`, event-macro Brier `0.19018`, early/late event Brier `0.18741`/`0.19296`,
absolute calibration gap `0.00463`, and largest-event squared-error share `0.04660`. Every fixed
gate passed. Independent freeze decision
`freeze-decision:3dbff2c63d7b9fe9de32d07b07ee3d6ec1c2272ed3b5b4d41f443b3e25497871`
sealed frozen system
`frozen-system:7b69995916de44043510c7d82a95b165d9aee6e2843d4bc00ca111808107b8eb`.
No protected evaluation was run by this packet.
