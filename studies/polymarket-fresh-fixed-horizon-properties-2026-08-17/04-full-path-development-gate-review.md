# Full-path development gate review

Recommendation: **REJECT FORMALIZATION — DO NOT REQUEST PROTECTED EVALUATION**.

This memo applies the repository's `review-backtest-gate` principles to the final predeclared
path-regime revision. It recommends; it does not grant a scientific permit, validation, promotion,
or durable question-memory status.

## Exact identity and scope

- Candidate:
  `authored-candidate:dc533e7d46b3c412139359ea7f83a70496b097b0e5965334dca896534df26436`.
- Development trial:
  `authored-development-trial:dc6da72433d4366e156f999a9662207fdbd940656d1596fe2db8243701fd96a2`.
- Development evidence:
  `authored-development-evidence:d8df309e4dd98a1273282e3408ba162ec10683df0f6375931b388cf8f583dec8`.
- Direct parent trial:
  `authored-development-trial:b92401ee03b8468d5284143987b66c7542ac33de6c4a94da5c5b257fbc5ba23c`.
- Environment: `bdl-polymarket-production-readonly`.
- Expanded snapshot:
  `polymarket-corpus:8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6`.
- Ancestor snapshot:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Derived formal catalog:
  `polymarket-corpus:75450ec954fb90615a016042804bb75cd7ef5ea6e729ddbd37d8916a72bdf4c1`.
- Partition: `2144b8338515271f342738c3ed7ad62565d98343c3e3284353780b436fbd9a40`,
  method `whole-event-chronological-fresh-replication/v1`.
- Driver SHA-256: `2fa36c181157ae8c1e09540f81b39350b289ca676cd1d5d232c392bcae6a47f3`.
- Authored candidate source SHA-256:
  `81f8db3766de4f4a58b6828c3e5c487eeccae6dea20e05d1a65850d4b08b22c4`.
- Receipt SHA-256: `185d727251db73a5199ea399790691c319713ca696b00cc24a6dc28a8e88ce0a`.

The target is two-cent reversal before two-cent continuation during 21 elapsed hours from the
delayed post-shock entry. The fixed 12-feature set and event-equal ridge-logistic recipe are in the
frozen driver. The sample contains the identical 423 declared earliest-per-market decisions used
by the parent trial. After the 100-row warm-up, the evaluator produced 319 OOF predictions from
319 markets and 117 events, with 149 positive and 170 negative labels.

## Legality and selection challenge

Satisfied checks:

- training rows enter only when `label_matured_at <= decision_time`;
- features read decision-time `market_probability` history, labels read only their legal outcome
  path, fitting reads admitted training rows, and prediction reads fitted state plus feature values;
- standardization, ridge-logistic parameters, and event weights are learned inside each replay
  boundary; prediction performs no fitting;
- one earliest eligible decision per market removes repeated-market label overlap;
- the exact feature set, target, penalty, four Newton steps, sample, metrics, and conjunctive gate
  were fixed before this evidence was generated;
- baseline, six-feature parent, and full revision use identical OOF row keys;
- 31 ancestor events and 47 protected events were unavailable; protected exposure and protected
  execution are both false;
- largest represented event supplies 6.90% of rows, below the fixed 20% concentration ceiling;
- the operational catalog-ordering failure and both scientific trials remain in ancestry.

Residual uncertainty remains substantial. The online replay may train on already-matured sibling
contracts from the same event, so it supports online cross-contract prediction rather than
untouched-event generalization. Retained probabilities are not executable quotes. The exploratory
success selected this target and feature family, and no protected evidence can repair development
instability.

## Predeclared gate result

The full model improved observation Brier from `.24402` to `.23828`, event-macro Brier from
`.24153` to `.23539`, late-half event Brier from `.25755` to `.24247`, pooled AP from `.60157` to
`.60925`, and won 71/117 events against the six-feature parent. Calibration, sample breadth,
absolute Brier, top-quintile lift, concentration, both-class counts, all baseline comparisons, and
the 60% event-win clause passed.

Two mandatory clauses failed:

- early-half event-macro Brier regressed from `.22524` to `.22818`;
- event-macro average precision regressed from `.90180` to `.89858`.

The gate is conjunctive. These are not optional diagnostics and cannot be removed after seeing the
result. Trying another subset, threshold, penalty, label, or aggregation inside this branch would
be a new selection-exposed hypothesis, contrary to the final-revision predeclaration.

## Protected plan and falsification condition

No protected plan is issued because the development candidate is not freeze-eligible. The fixed
falsification condition was failure of any mandatory development clause; two clauses failed. The
47-event protected block therefore remains sealed and available for a future candidate arising
from independently justified evidence, not for another revision of this exhausted branch.

Only independent governance could authorize protected evaluation, and only independent validation
could promote a resulting finding. This candidate should not be submitted to either gate.
