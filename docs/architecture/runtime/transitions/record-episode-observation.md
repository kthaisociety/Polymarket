# episode.record-observation — StructuredObservation → active ResearchEpisode working evidence

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Make a substantive observation durable within the current investigation so later turns can use it, while preserving the rule that observation is not committed `ResearcherState`.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I9, I11–I13, I16–I17, I25.
- `docs/specification/STATE_CONTEXT_AND_MEMORY.md`, tool result is not belief update and semantic commit boundaries.
- `docs/specification/DECISIONS.md`, Research loops and State/context architecture.

## Source A

One authoritative `StructuredObservation`, its action/execution/provenance/artifact correlation, and the exact expected active episode identity/version.

## Destination B

The same active `ResearchEpisode` with one ordered, provenance-bearing working-evidence entry whose bounded substantive meaning, status, warnings, and drill-down refs are reconstructible.

## Mapping f

Validate exact session/episode identity, active lifecycle, expected version, and observation correlation; append the observation meaning and refs atomically/idempotently to working evidence; append progression history; leave durable state unchanged.

## Must preserve

- observation/action/execution identity and order;
- substantive payload, status/type, warnings, recoverability, provenance, and artifact refs;
- episode/session/task/environment identity and current lifecycle;
- provisional/working epistemic status.

## May transform

- observation representation into an episode evidence entry;
- duplicate exact delivery into the original append result;
- large detail into retained references while keeping decision-relevant meaning.

## Must exclude

Implicit state delta, durable conclusion, gate passage, finding promotion, unrelated-session content, latest-episode substitution, raw artifact duplication, capability/provider write authority, history rewrite, and ID-only persistence.

## Authority boundary

The runtime progression boundary validates and appends. Capabilities/providers cannot write episodes. State validators/commit coordinator alone may later change `ResearcherState`.

## Allowed state mutation

Append one working-evidence/progression entry to the exact active episode and bounded trajectory observability.

## Forbidden state mutation

No `ResearcherState`, task, evidence-ledger, permission, exposure, gate, finding, or episode lifecycle change merely because the observation arrived.

## Failure semantics

Foreign/stale/missing/terminal episode, invalid observation correlation, or persistence failure rejects the append and leaves episode/state coherent. Exact retry does not duplicate evidence; changed payload under the same delivery identity conflicts. A successful turn cannot acknowledge progression while evidence is unreconstructible.

## Observable consequences

After transient objects disappear, reloading the episode exposes the observation's row count/warnings/provenance and exact order; `ResearcherState` identity/version/content is unchanged.

## False-success implementations considered

- Store only observation ID.
- Append to whichever episode is active.
- Copy the observation summary into durable state.
- Resolve or suspend the episode based on observation status.
- Acknowledge before durable append or duplicate on retry.

## Falsifying tests

1. Append an observation, discard transient objects, reload through episode APIs, and assert substantive meaning/provenance/order plus byte/semantic equality of prior state. **Level B.**
2. Pair exact-current and foreign/stale episode targets; only current appends, with no latest substitution.
3. Inject persistence failure and retry; assert no acknowledged missing evidence and exactly one append after recovery.
4. Replace stored payload with ID-only entry and feed reconstruction through context.build-packet; the required next-decision facts must be unavailable and the test red.

## Mutation-sensitivity check

**Mutation:** persist only `observation_id` and `artifact_refs`.

**Expected failure:** test 1 becomes red because row count/warnings/provenance meaning cannot be reconstructed from the episode.

## Composite dependencies

observation.assemble-authoritative-result supplies authoritative observations; context.build-packet reconstructs context; runtime.continue-from-observation proves causal feedback; commit.compose-request–commit.publish-boundary govern later semantic commit; trajectory.append-event records progression.

## Fundamentals review

`CONSISTENT`. The seam preserves the fast research loop and durable working evidence without collapsing temporary observation into committed belief.

## Grill findings

Resolved non-semantically: added exact-version targeting, idempotent delivery, and acknowledgement-after-durable-append requirements.

## Remaining user decisions

None. Episode storage layout and entry representation remain free.
