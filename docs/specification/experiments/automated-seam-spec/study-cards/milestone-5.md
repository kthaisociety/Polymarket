# Milestone-5 study cards

## training.fit-system — frozen recipe + legal W_t → FitRecord + immutable fitted system F_t

**Why does it exist?** Fit every learned quantity only inside the legal window under the exact frozen procedure.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Recipe and window identities, all preprocessing/selection/model/ensemble learned state, seeds/environment, failures.

**Most dangerous false success?** Fit preprocessing on all S_t before selecting W_t.

**Which test catches it?** Poison outside W_t and assert identical fit; inspect all learned provenance; induce component failure and require no F_t/fallback. **Level A/B.**

**Any unresolved human decision?** None.

## prediction.generate-record — F_t + legal current features from I_t → PredictionRecord

**Why does it exist?** Produce an immutable prediction without learning while preserving exact system/time/information identity.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Prediction semantics/value, all identities, decision time, inputs/vintages, environment, uncertainty/warnings.

**Most dangerous false success?** Update scaler statistics during predict.

**Which test catches it?** Snapshot every learned state, fail-on-fit/update/outcome, exact-version test. **Level A/B.**

**Any unresolved human decision?** None.

## outcome.record-mature-label — mature realized target → immutable OutcomeRecord

**Why does it exist?** Record realized outcome separately and only when TargetDefinition says it is legally complete/available.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Target/prediction IDs, value/unit, time semantics, vintage/revision, environment, provenance.

**Most dangerous false success?** Use reference timestamp as maturity.

**Which test catches it?** Maturity boundary and revision-lineage tests. **Level A/B.**

**Any unresolved human decision?** None.

## development.evaluate-candidate — candidate + development protocol/data → development evidence/diagnostics

**Why does it exist?** Generate iterative evidence while keeping it clearly development-grade and temporally legal, not protected validation.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Candidate/protocol/fold/time/data identities, metrics uncertainty/caveats, failures, selection ancestry, development status.

**Most dangerous false success?** Use shuffled CV and report best trial only.

**Which test catches it?** Temporal adversarial folds, fail-on-protected access, all-trials retention. **Level A/B.**

**Any unresolved human decision?** None.

## development.revise-candidate — development diagnostics → interpretation + revised candidate

**Why does it exist?** Close development feedback causally while recording every trial and creating new identity when scientific meaning changes.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Diagnostic substance/status, candidate identity, rationale, trial/exposure ancestry, failed paths.

**Most dangerous false success?** Choose revision by scripted turn count.

**Which test catches it?** Paired Level C diagnostic feedback, no store access, transcript deletion, ancestry assertions.

**Any unresolved human decision?** None.

## training.block-invalid-fallback — frozen fitting failure → typed block or predeclared fallback

**Why does it exist?** Prevent failure from silently changing preprocessing/model/feature procedure.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Original procedure, failure, trigger, fallback identity/order, window/environment, status.

**Most dangerous false success?** Automatically reduce PCA components to available rank.

**Which test catches it?** Induce failure with/without declared fallback; assert block versus exact fallback identity. **Level A/B.**

**Any unresolved human decision?** None.

## ledger.record-trial-lineage — development trials/candidate lineage → ResearchLedger ancestry

**Why does it exist?** Preserve selection history so survivors are not presented as untouched first trials.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** All trial identities/order, parentage, protocols/data periods, outcomes/failures, selection rationale/status, environment.

**Most dangerous false success?** Delete losing trials after selection.

**Which test catches it?** Run multiple trials including failures/rejection, select one, assert complete graph and immutable correction. **Level A/B.**

**Any unresolved human decision?** None.
