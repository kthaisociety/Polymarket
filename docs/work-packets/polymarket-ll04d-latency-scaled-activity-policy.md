# Work packet

## Identity

- Packet: LL-04d latency-scaled activity policy
- Owning architecture block: Data foundation and authored low-latency investigation
- Semantic transition or responsibility: one exact H3/H5 parent definition plus one dimensionless
  activity policy to a fixed parent-bound LL-04a gate definition
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the uncommitted
  low-latency corpus, H1/H3/H5, LL-00, LL-04a/b/c, and acquisition packets in this worktree

## Objective

Predeclare one activity-gate candidate whose elapsed thresholds scale with the parent strategy's
declared action delay, without inspecting L2 values, fitting cutoffs, or copying sampled-price time
scales.

## Context boundary

- Global authority loaded: repository and Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, semantic architecture map, and time-series feature-design principles.
- Owning block and transition contract: data-foundation `README.md`, transition index,
  `IMPLEMENTATION.md`, `data.build-information-set`, and LL-00/LL-04a/b/c packet contracts.
- Relevant adjacent interfaces: H3/H5 parent definitions and declared action delays,
  `ActivityParticipationGateDefinition`, `ActivityGateCampaignDefinition`, and the sampled-process
  activity ancestry.
- Explicitly excluded work: measured-latency estimation, threshold fitting/search, alternative
  policy trials, quote-value access, strategy replay, campaign scoring, maker behavior, fill/queue
  simulation, formal validation, protected evaluation, and live trading.
- Assumptions: the parent action delay is a declared replay policy, not measured production
  latency. A zero-delay parent cannot define positive latency-scaled elapsed windows and must fail.

## Candidate memo

### Exact question and ancestry

For an unchanged H3 or H5 taker strategy, does participating only when the preceding source-message
burst is active on the same scale as the declared action delay improve the LL-04c primary
collateral-time diagnostic relative to complete history and both component rivals?

Prior sampled-process evidence supports a duration-dependent update mechanism but supplies no
seconds-level L2 cutoff. LL-04d therefore chooses a dimensionless relation to the strategy's own
declared reaction scale. The policy is a new quote-based hypothesis, not a fitted descendant of the
rejected protected arrival candidate.

### Fixed candidate identity

The only primary policy in this packet is `ll04d-latency-scaled-primary-v1`:

- `maximum_quiet_duration = 1 × parent action_delay`;
- `recent_window = 5 × parent action_delay`;
- `minimum_recent_source_event_count = 2`, excluding the current source-message burst as in LL-00.

Interpretation: the previous distinct reference-leg update must have arrived within one declared
reaction interval, and at least two prior venue source messages must have arrived within five such
intervals. The joint rule identifies a recent burst without treating the triggering message as its
own history. It may capture fast information propagation or merely adverse selection; either sign
is possible.

### Decision, target, maturity, and rivals

- Decision, parent attempts, target, maturity, costs, holding horizon, and missingness remain exactly
  LL-04a/b/c.
- The parent definition's full recipe, scope, reference leg, and definition ID enter derived gate
  identity. A changed parent creates a different gate definition.
- LL-04b complete-history, quiet-only, recent-activity-only, and joint populations remain mandatory.
- LL-04c must use a joint-versus-rival primary contrast and retain chronological missingness,
  early/late stability, and concentration.
- There is no threshold training window because this candidate performs no fitting or selection.

### Trial budget and stopping rule

Trial budget: one latency-scaled policy. No alternative multiplier or count threshold may be tried
inside this candidate after quote values are inspected. A meaning-changing revision receives a new
policy ID and parent-trial ancestry.

Reject or revise if the derived policy is operationally sparse, fails either component rival, has
non-positive pooled or block-macro collateral-time value, fails an early or late chronological
half, concentrates in one block/market, or fails later execution evidence. Passing development
only permits a separately authored paper-execution study.

Recommendation before data: `EVALUATE` this one candidate after capture; do not call it useful.

## Change boundary

- Permitted files or components: one activity-policy module and adversarial test, public exports,
  data-foundation implementation map, low-latency hypothesis/status documentation, and this packet.
- Allowed state effects: none; derivation returns an immutable gate definition.
- Forbidden state effects: data access, fitting, selection, parent mutation, implicit defaults,
  strategy execution, research-state promotion, protected exposure, or trading authority.

## Correctness

- Governing invariants and decisions: I1 temporal admissibility, I2 fitted-state legality, I5
  identity, I6 no fallback, I10 mission stability, I11 immutable evidence, I12 trial ancestry, I13
  provenance, I17 explicit failure, I21 evaluation is not training, and I24 environment identity.
- Concrete failure modes: using wall-clock constants unrelated to parent latency; accepting a zero
  action delay; rounding elapsed durations; deriving from gate/test defaults; losing parent/scope/leg
  identity; permitting quiet duration beyond the recent window; or silently changing the named
  primary policy after results.
- Expected inputs and outputs: exact H3 or H5 parent definition and explicit latency-scaled policy;
  exact parent-bound LL-04a gate definition with elapsed thresholds.
- Violating mutation or counterexample: change H3 action delay from one to two seconds while leaving
  derived windows unchanged; the gate silently ceases to represent its declared dimensionless rule.
- Required local tests/evals: policy validation, exact named-candidate values, H3/H5 derivation,
  microsecond-exact multiplication, zero-delay rejection, parent/scope/leg binding, changed-parent
  identity, no mutation, and LL-04c campaign-definition composition.
- Required integration evidence: LL-00/LL-04a/b/c/H3/H5 tests, full Polymarket adapters,
  proportionate Chronos tests, strict static checks, docs generation, and `git diff --check`.

## Completion evidence

- Named primary policy and generic explicit derivation API exist without defaults or fitting.
- Deterministic adversaries prove timing arithmetic, identity, H3/H5 composition, failure, and
  campaign compatibility.
- Focused, Polymarket, and proportionate Chronos suites plus strict static checks pass.
- Architecture and hypothesis status state the single-trial budget and declared-versus-measured
  latency distinction.
- A transition receipt records hashes, verification, and empirical dependencies.

## Boundary revisions

None.

## Transition receipt

### Result

- Packet: LL-04d latency-scaled activity policy
- Status: `COMPLETE`
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the recorded
  uncommitted low-latency program
- Resulting repository state: one exact no-fit latency-scaled activity candidate and deterministic
  H3/H5 parent-bound gate derivation

### Delivered state delta

- `ll04d-latency-scaled-primary-v1` fixes recent-window multiplier `5`, maximum-quiet multiplier
  `1`, and minimum prior source-event count `2` with no defaults or alternative trial grid.
- Derivation rejects non-positive parent action delay, preserves exact elapsed arithmetic, and binds
  parent kind, full-definition hash, definition ID, scope, reference leg, and derived thresholds.
- The resulting gate fields compose directly with LL-04c campaign identity.
- No source data, fitting, threshold selection, strategy replay, research state, protected evidence,
  or trading state changed.

### Evidence

- Seven focused LL-04d adversaries passed.
- Eighty-three adjacent LL-00/LL-04/H3/H5 tests passed.
- The full Polymarket adapter suite passed: 158 tests.
- The proportionate Chronos suite passed: 527 tests, excluding only the two documented sandbox
  modules that require local HTTP behavior.
- Ruff formatting/checking across 38 Polymarket adapter files and full basedpyright passed.
- Adversaries prove the named candidate values, microsecond-exact multiplication, H3/H5 kind and
  recipe composition, zero-delay denial, threshold-geometry denial, full-parent mutation-sensitive
  identity, deterministic replay, and LL-04c campaign compatibility.
- Policy source SHA-256:
  `da26829679888ef77512a8b47accde2ccea7777d40790d0c6d1a72b1e377b869`.
- Policy test SHA-256:
  `4adfa1abdc2ade48b06e0e2eac92f4e9067608b577e61da27983cd71a7cf333e`.

### Knowledge carried forward

- The candidate tests an activity burst on the strategy's declared reaction scale rather than
  asserting a universal seconds threshold or copying sampled-process parameters.
- A passing displayed-touch campaign would only justify a separately authored paper-execution
  study; the declared action delay still requires replacement by measured production latency.
- Remaining dependencies are a deployed collector, retained production L2 corpus, executable
  campaign advancement standards, semantic event grouping, fees, measured order latency, fills,
  and partial-fill evidence.
- This receipt proves deterministic candidate identity and derivation only. It does not prove the
  activity mechanism, economic value, execution, formal eligibility, or trading authority.
