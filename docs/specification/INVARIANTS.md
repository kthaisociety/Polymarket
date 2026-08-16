# Non-Negotiable Invariants

This is the shortest high-authority specification of what the implementation must never silently violate.

For each invariant, maintain at least one executable test/eval before considering the relevant subsystem complete.

## I1 — Temporal admissibility

At simulated time `t`, no computation that claims to represent knowledge at `t` may access an observation whose `available_at > t`.

Row/reference timestamp alone does not establish admissibility.

## I2 — Learned state is information

Any learned/fitted quantity must be fitted only from information legally available inside the corresponding training boundary.

This includes preprocessing, feature selection, PCA, hyperparameters, auxiliary models, and ensemble weights.

## I3 — Prediction does not learn

`predict()` and equivalent inference paths cannot fit, update, select, or adapt model/preprocessing state unless the predictive system definition explicitly defines a different online-learning protocol.

Default behavior: no learning during prediction.

## I4 — Protected backtest requires frozen scientific identity

A true protected backtest cannot run on an unfrozen or incompletely specified predictive system.

## I5 — Frozen identity is immutable

A change that alters the experiment's scientific meaning creates a new definition/version/candidate.

A frozen object cannot silently mutate in place.

## I6 — No silent scientific fallback

Formal machinery cannot silently substitute a different feature/model/fitted transform/procedure when the frozen procedure fails.

Fallback is allowed only when that fallback itself was predeclared in the scientific specification.

## I7 — Protected exposure is irreversible epistemic history

Once protected evidence is exposed to the research process, it cannot later be represented as fresh/unseen evidence for a modified candidate.

## I8 — Privileged actors cannot self-authorize

The agent/candidate creator may request protected backtest, finding promotion, and lesson promotion, but cannot grant itself the privileged decision.

## I9 — Observation is not durable belief

A raw tool result or intermediate observation cannot directly mutate committed `ResearcherState`.

Working evidence enters the active research episode. Durable state changes occur at semantic commit boundaries through a validated state-update path.

## I10 — Mission cannot silently drift

Material changes to target/horizon/research identity require explicit task respecification/versioning.

The horizon identity includes elapsed-versus-calendar kind and every declared calendar policy.
Replacing a calendar month/quarter with a fixed day count is a material change, even when the two
coincide at one anchor.

Changing hypotheses/features within the same problem does not require a new `ResearchTask`.

## I11 — Immutable evidence records remain immutable

Completed `BacktestRun`, prediction/outcome records, validation decisions, and append-only ledger history cannot be rewritten to improve a result.

Corrections create explicit new records/versions with lineage.

## I12 — Rejected evidence remains history

Rejected experiments/findings are not deleted merely because they failed. Trial ancestry and prior exposure matter scientifically.

## I13 — Provenance follows scientific claims

A promoted finding or durable lesson must carry enough evidence/provenance references to identify what data periods/experiments support it.

## I14 — Context cannot bypass permissions

`ContextBuilder`/retrieval may not surface evidence/data that the current epistemic/capability state forbids the agent from seeing.

## I15 — Compaction does not destroy evidence

Context compression may change what is immediately visible, but underlying trajectory/evidence/artifacts remain accessible according to permissions.

## I16 — Current state beats stale interpretation

Retrieval/context must preserve version/current/superseded semantics so an old interpretation is not silently presented as the current belief.

## I17 — Formal failure blocks false success

If a formal operation fails, downstream code cannot continue as if the expected scientific object/result exists.

## I18 — Exploratory freedom does not grant side-effect freedom

The AI may write open-ended research code, but sandbox policy controls data domain, filesystem/process/network side effects, secrets, protected data, and privileged stores.

## I19 — Report presentation cannot alter scientific substance

Report wording/layout cannot change validation status, evidence, caveats, provenance, or scientific conclusion encoded in `ValidatedFinding`.

## I20 — Model provider is replaceable

Scientific modules/runtime state must not depend irreversibly on a particular provider's session transcript, auth object, or response type.

## I21 — Evaluation is not training

Evaluator/validator code may measure evidence but cannot retrain/reselect the system whose protected evidence it is evaluating.

## I22 — Development and protected evidence have different epistemic status

Development evidence may drive iterative candidate revision. Protected evidence cannot be treated as another ordinary tuning fold after exposure.

## I23 — Legal target maturity

A supervised training example may enter `S_t` only if its target/outcome is legally complete/available at simulated time `t` according to `TargetDefinition`.

## I24 — Environment identity is explicit

Scientific/research state should reference the environment/data/schema versions under which evidence was produced. Later environment changes cannot retroactively change historical meaning.

## I25 — Runtime retries do not duplicate irreversible effects

Retrying model/provider/operational calls must not accidentally duplicate privileged actions, state commits, ledger promotions, or protected exposure.

## I26 — Predictor availability and label maturity are separate boundaries

At every simulated decision time, the backtest rebuilds the legal current-information boundary `I_t` and the completed supervised-sample boundary `S_t` from their own temporal semantics. Newly released predictor information and newly matured target labels must not be conflated into one generic "new data" event.
