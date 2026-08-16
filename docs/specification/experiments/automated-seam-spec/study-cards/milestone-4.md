# Milestone-4 study cards

## formalization.create-candidate — hypothesis/exploratory idea + evidence → candidate feature/model

**Why does it exist?** Make scientific candidacy explicit, versioned, and ancestry-bearing rather than promoting an interpretation or artifact implicitly.

**Which fundamental does it protect?** `CONSISTENT`: implied candidate mapping uniquely follows the promotion funnel.

**What must cross?** Hypothesis meaning, evidence status/provenance, task/environment, assumptions, ancestry.

**Most dangerous false success?** Treat any temporary model artifact as a formal model candidate with no ancestry.

**Which test catches it?** Pair same hypothesis with different evidence ancestry; assert distinct provenance and provisional status. Try artifact-only promotion; reject. **Level A/B.**

**Any unresolved human decision?** None.

## feature.define-identity — candidate feature + semantics → FeatureDefinition

**Why does it exist?** Promote exploratory computation into a reproducible, time-legal feature identity.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Scientific mapping, dependencies, lags/windows, availability, units/output, missingness, fitted procedure, provenance.

**Most dangerous false success?** Exclude fitted-state semantics from identity.

**Which test catches it?** Omit each semantic and require failure; mutate each meaning dimension and require new identity; fail-on-fit. **Level A/B.**

**Any unresolved human decision?** None.

## feature.compile-definition — FeatureDefinition → exact FeatureExpression / computation graph

**Why does it exist?** Compile stable feature meaning into executable representation without semantic substitution.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Definition identity, operator parameters/order, fields, time semantics, missingness, fitted boundaries, compiler version.

**Most dangerous false success?** Drop Lag node while retaining feature ID.

**Which test catches it?** Adversarial definitions where lag/drop/log order changes outputs; compile and compare semantic interpreter, fail unsupported. **Level A/B.**

**Any unresolved human decision?** None.

## feature.materialize-definition — FeatureDefinition + legal environment → provenance-bearing FeatureSeries

**Why does it exist?** Materialize exact formal feature values under a named legal data environment without future access or global fitting.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Definition/version, times, values/units, dependencies/vintages, environment, fitted-state/window ID, missingness/caveats.

**Most dangerous false success?** Fit missing scaler on all available data.

**Which test catches it?** Publication-delay/revision fixture, fail-on-fit, missing dependency explicit failure, exact lineage. **Level A/B.**

**Any unresolved human decision?** None.

## feature.assemble-set — selected FeatureDefinitions → versioned FeatureSet

**Why does it exist?** Preserve exact feature membership/versions/order semantics used by a candidate system.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Exact members/versions, selection ancestry, output names/order where meaningful, environment constraints.

**Most dangerous false success?** Resolve member refs to latest versions.

**Which test catches it?** Same names/different versions and order-sensitive model fixture; assert exact identity. **Level A.**

**Any unresolved human decision?** None.

## feature.revise-from-diagnostics — FeatureAnalysis + interpretation → candidate revision/rejection/formalization decision

**Why does it exist?** Let diagnostics causally influence feature research while keeping analysis evidence distinct from the feature definition and recording trial ancestry.

**Which fundamental does it protect?** `CONSISTENT`: implied feature loop follows locked evidence distinction.

**What must cross?** Diagnostic substance/status/protocol, candidate identity, rationale, ancestry, rejected paths.

**Most dangerous false success?** Base decision only on headline correlation.

**Which test catches it?** Paired same headline/different stability diagnostics, transcript loss, provider only packet; assert formalize vs revise/reject and ancestry. **Level C.**

**Any unresolved human decision?** None.

## model.define-recipe — candidate model/recipe → ModelDefinition

**Why does it exist?** Formalize a reproducible model and selection recipe distinct from learned fitted state.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Algorithm, parameters/search procedure, preprocessing, randomness, compatibility, training protocol refs, provenance.

**Most dangerous false success?** Embed fitted coefficients in ModelDefinition.

**Which test catches it?** Fail-on-fit, inspect absence of learned state, vary each semantic dimension and assert identity. **Level A/B.**

**Any unresolved human decision?** None.

## model.define-ensemble — selected model definitions/method → EnsembleDefinition

**Why does it exist?** Freeze ensemble membership and combination method separately from learned weights.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Members/versions/order, method, fixed vs learned weights, training procedure, provenance.

**Most dangerous false success?** Store learned weights in definition from exploratory full data.

**Which test catches it?** Fail-on-fit; inspect identity variants; insufficient weight semantics fails. **Level A/B.**

**Any unresolved human decision?** None.

## system.assemble-definition — target + FeatureSet + models/ensemble + protocols → PredictiveSystemDefinition

**Why does it exist?** Assemble every choice changing experimental meaning into one versioned candidate identity.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** All component versions, target/feature/model/ensemble/training/evaluation semantics, environment, ancestry, status.

**Most dangerous false success?** Omit preprocessing/selection procedure from system identity.

**Which test catches it?** Vary each material dimension and assert identity; reload after newer components; fail-on-fit/freeze. **Level A/B.**

**Any unresolved human decision?** None.

## formalization.version-material-change — material formal-object change → new version/candidate with lineage

**Why does it exist?** Prevent in-place mutation or disguised experiment changes while allowing representation-only edits that preserve meaning.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Parent content/identity, exact diff, ancestry, prior evidence/trials/exposure, environment/provenance.

**Most dangerous false success?** Mutate frozen/component object in place while retaining ID.

**Which test catches it?** Change lag, field, missingness, model, protocol and assert new versions; reorder serialization and assert semantic equivalence; old refs unchanged. **Level A/B.**

**Any unresolved human decision?** None.
