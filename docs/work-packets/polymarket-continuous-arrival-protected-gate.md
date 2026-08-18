# Gate memo: continuous Polymarket arrival hazard

## Recommendation

`REQUEST_INDEPENDENT_ASSESSMENT` for the exact source-18 frozen candidate. This memo recommends;
only independently configured governance, resource, exposure, evaluation, and validation services
may authorize or resolve the request.

## Exact identities

- Candidate:
  `authored-candidate:10b63992c977425e8b92bcc8d510a753775c1ed3708c89cbeff27734819b9de9`.
- Candidate source SHA-256:
  `2829c87de47566d8fe383cf2b75a69aefcfc1a81f4f84c5c54308cc46762878a`.
- Development evidence:
  `authored-development-evidence:59ac537cb54a61360d7662a3e921178d7a79261ed2379890d5b16bc2d14bb60a`.
- Frozen system:
  `frozen-system:7b69995916de44043510c7d82a95b165d9aee6e2843d4bc00ca111808107b8eb`.
- Development receipt SHA-256:
  `417e7c9de63538f558a1cdd97609d6d6c82a49b7195bebaee830f8aafec0f192`.
- Protected plan:
  `authored-protected-plan:691e74db76eb262808b111e83956f23b462745c51b4e2e5d4e8233b27595f962`.
- Protected scope:
  `protected-scope:43a11e49d3da8c97ee05f94cd6a2ff1304aaebdf303b6ba81e359bc395f49f02`.
- Exposure before this request: none; source 18 records `protected_values_exposed=false`.
- Frozen protected-resolution driver SHA-256:
  `d707661767f058c8233b3810db71e18c7c87c5ca0832598888848a7dc8a5d342`.

Aliases such as “latest,” “best,” or “arrival model” are not accepted identities.

## Candidate and claim

At each eligible metadata-fixed decision, predict whether the next registered Polymarket
probability sample 45–75 minutes later changes. Features are current probability, boundary
distance, winsorized logit level, continuous log quiet run, and prior-24 zero fraction. Fold-local
scaling and logistic coefficients use event-equal fitting, ridge penalty `0.1`, and four Newton
updates. Prediction performs no fitting.

The claim is limited to sampled-move probability on the exact retained final-47-event schedule. It
does not concern direction, resolution, objective probability, latent belief, trades, quotes,
execution, alpha, or profit.

## Development and selection audit

Satisfied checks:

- predictor history and next-sample label use distinct legal time boundaries;
- 25 regular past observations are required before a key is admitted;
- the target matures only on a legal next regular sample;
- learned means, scales, and coefficients are fitted inside temporal training windows;
- source 17 replayed the fully reconstructible hazard without fitting on 17,671 later predictions;
- source 18 passed all fixed formal gates over 202 OOF predictions and 100 events;
- early/late Brier, calibration, and concentration passed;
- exact candidate, evidence, plan, and freeze identities are sealed;
- the coarse-cell source-14 rejection remains retained and unmodified.

Selection burden and unresolved uncertainty:

- this is the second formal arrival candidate after observing the coarse-cell rejection;
- the continuous feature family was supported before that rejection, but returning to it is still
  explicit trial ancestry rather than a pristine first test;
- 202 OOF predictions are only two above the fixed feasibility floor;
- the later successor cohort supported distinct earlier process analyses and is not protected;
- the sampled observation process may create staleness even if latent beliefs update differently;
- the protected standard is absolute and contains no executable comparator or trading metric.

No plausible future-data access, label leakage, fit-during-prediction, protected exposure, or
identity mutation was found. These checks justify falsification, not expected success.

## Exact protected plan

- Resource: retained main expanded corpus, original final 47 whole events, exact projected catalog
  identity in the source-18 content manifest.
- Decisions: 100 predeclared protected keys after past-only regular-history eligibility; no key may
  be added, replaced, or skipped silently.
- Scenario: historical walk-forward with expanding training over all declared candidate keys,
  minimum 100 training rows, exclusion only through the declared missingness policy.
- Refit policy: the exact authored program refits only as specified by the expanding scenario;
  transforms and logistic coefficients remain training-window local.
- Metrics: MSE/Brier, MAE, coverage, and failure rate; stability and squared-error concentration.
- Promotion criteria: MSE at most `0.20`, MAE at most `0.40`, coverage at least `0.95`, failure
  rate at most `0.05`, absolute-error stability standard deviation at most `0.30`, and maximum
  squared-error concentration at most `0.05`.
- Claim and caveats: exactly the plan and claim-template identities listed above.
- Recipient: `researcher:chronos-polymarket-continuous-arrival`.
- Exposure: record exactly once before the protected catalog is loaded; exposure is irreversible.
- Failure treatment: every declared decision remains in the run as a decision or typed failure.
- Output: one sealed run, report, validation decision, and either finding or protected negative.

## Falsification condition

Any safe denial, identity mismatch, execution-invalid report, missing decision coverage, metric or
stability/concentration criterion failure, or independent validation rejection falsifies promotion
of this exact candidate. After disclosure, no threshold, feature, model, decision, claim, or report
may be repaired or reinterpreted into success. The exposed period cannot be reused as fresh
development data.

## Resolution

**COMPLETE — PROTECTED NEGATIVE; EXACT SYSTEM REJECTED.** Independent governance authorized one
exposure and the ledger records, in order, authorization, one protected disclosure, one sealed run,
measurement, validation rejection, and negative-result retention. The exact protected receipt is
`studies/polymarket-stochastic-process-paper-2026-08-18/protected-receipts/19_continuous_arrival_hazard_protected_resolution.json`;
its SHA-256 is `4e9fa014c774fda83eaa8f4d7f75ec838b913197d7a14778a3333518e430b60d`.

The run retained all 100 declared decisions. Sixty-five produced predictions; 34 failed with
`training_window_not_ready` and one with `outcome_unavailable`. MSE `0.189254`, MAE `0.394489`, and
absolute-error standard deviation `0.183390` met their fixed standards. Coverage `0.65` failed the
`0.95` floor, failure rate `0.35` failed the `0.05` ceiling, and maximum squared-error concentration
`0.054852` failed the `0.05` ceiling. Validation therefore rejected the system and retained
negative result
`negative-result:f9b794e38b9b317f867605fd0cfcfafd46caa29189a72c034ac6798b25b9e9fe`.

No result, threshold, schedule, or candidate is repaired after exposure. The 65 completed rows are
reported as suggestive conditional performance only; their non-random missingness prevents a
protected predictive claim. The exposed holdout is not reusable as fresh development data.
