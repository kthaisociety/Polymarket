# Automated evaluation-specification experiment summary

The experiment has become a production-facing L3/L4 verification framework. It executes proof
adapters for compositions that exist and preserves explicit reds for those that do not.

## Outputs

- 15 HIGH-risk deterministic composite propositions in `COMPOSITE_TEST_REGISTER.md`.
- 12 behavioral scenario families in `BEHAVIORAL_EVAL_REGISTER.md`.
- 36 generated opaque harness fixture envelopes per seed (three per family); the substantive
  Level-D scientific scenario generators remain future work.
- Proof schemas, adapter registry/runner, behavioral generator/grader, and status reporting in
  `src/research_agent/verification/`.
- 10 catalog-validated production `HARNESS_GREEN` compositions and 5 intentional application
  `EXPECTED_RED` compositions.
- 59 verification tests passing across proof classification and 12 behavioral fixture families.
- 0 architecture gaps, user decisions, test-insufficient items, unexpected greens, or harness bugs.

## Strongest protections

- Intermediate causal propagation rather than endpoint ordering.
- Authority-bound semantic commits whose episode, state, result, and event are observed together,
  with stage-fault rollback, exact retry/replay, and changed-payload conflict mutations. This proves
  in-process atomic publication, not crash-durable persistence.
- Authorized exploratory meaning, transcript-free checkpoint reconstruction, and same-episode
  failure repair are proven by paired production worlds with access/artifact/failure provenance;
  the deterministic packet-only fixtures do not establish provider or researcher quality.
- Independent predictor availability and label maturity.
- Exact frozen identity and authority binding.
- Authority-issued workflow and protected-resource bindings: caller-substituted authority labels,
  same-label fake capabilities, and changed protected binding/catalog all fail before disclosure.
- Exposure recorded at disclosure, including failed runs.
- Transcript-free context reconstruction.
- Failure repair without scientific meaning corruption.
- Opaque fixture identities, evaluator-private shuffled truth, and explicit separation between
  harness-causality grading and future researcher-quality evidence.
- Behavioral transfer measured with a fixed underlying model, including harmful-overgeneralization controls.

## Implementation meaning

Verdict: continue incremental implementation against the 5 remaining reds and upstream contracts.
An application green means a catalog-owned oracle validated raw production traces for the exact
named components and assertions; behavioral fixture runs never establish real-model researcher
quality. The 10-green/5-red split is retained only after recalculating the strengthened authority
oracle; it does not prove durable registries, external identity attestation, live protected-data
integration, autonomous workflow authorship, or validated learning.
