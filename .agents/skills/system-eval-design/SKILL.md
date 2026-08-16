---
name: system-eval-design
description: Derive architecture-traceable composite deterministic tests and behavioral AI-eval families from existing seam contracts without inventing product semantics. Use after seam contracts exist and before production implementation, when designing L3 system compositions, L4 real-model evaluations, expected-red executable specifications, eval registers, or implementation-readiness evidence. Classify every item as DETERMINISTIC_COMPOSITE_TEST, BEHAVIORAL_EVAL, or ARCHITECTURE_GAP.
---

# System Eval Design

Derive downstream verification from upstream architecture. Never change architecture for test or grader convenience.

## Establish authority

1. Read repository instructions and authority order.
2. Read the exact invariants, decisions, contracts, and seam rows governing the proposition.
3. Treat locked architecture and canonical seams as authority. Label experimental seam candidates as provisional inputs.
4. Trace every assertion to an invariant and/or seam contract. Classify an untraceable assertion as `ARCHITECTURE_GAP`; do not adopt it.
5. Use canonical vocabulary. Do not create product concepts, gates, scores, or authority roles for the harness.

## Classify before designing

Choose exactly one:

- `DETERMINISTIC_COMPOSITE_TEST`: the harness can know the correct result exactly across two or more seams.
- `BEHAVIORAL_EVAL`: correctness depends materially on open-ended model judgment, investigation, or calibrated scientific behavior.
- `ARCHITECTURE_GAP`: the expectation lacks an authoritative upstream basis or requires a new semantic choice.

Do not use an LLM judge for facts Python can determine. Do not disguise missing production semantics as an eval rubric.

## Derive deterministic composites

1. Traverse paths `A -> B -> C` where local arrows do not prove the system proposition `A -> C`.
2. State `P(A) => Q(C)` and cite every governing source.
3. Define the deterministic oracle, fixture world, expected and forbidden results, and observable intermediate propagation.
4. Name the weakest plausible false-success implementation.
5. Construct a counterfactual or violating mutation that definitely turns the test red.
6. Exclude side channels to original input, hidden truth, privileged fixtures, and evaluator state.
7. Reject endpoint-only evidence. Prove information, identity, authority, time, or state constrained the composition.
8. Use [composite-template.md](references/composite-template.md).

For HIGH risk, require a discriminating pair: vary the governing world fact, hold alternatives fixed, and require the contractually relevant output to change or remain invariant.

## Derive behavioral families

1. Trace a researcher capability to the product objective and architecture.
2. Design a scenario distribution, not a memorisable puzzle; randomize surface form while preserving capability.
3. Prefer similar visible evidence with different hidden scientific truth.
4. Keep generator labels and evaluator truth inaccessible to the agent.
5. Grade epistemic outcomes, evidence, calibrated claims, progress, efficiency, and violations—not a prescribed method.
6. Separate objective signals from genuinely semantic signals. Use deterministic graders first; bind any LLM judge to structured evidence and test robustness.
7. Prevent blanket acceptance, rejection, uncertainty, and endless analysis from scoring well.
8. Keep hard architecture violations as hard failures.
9. Use [behavioral-template.md](references/behavioral-template.md).

## Design executable red evidence

After review, implement only fixtures, generators, fakes, schemas, graders, runners, reports, and expected-failure tests. Do not implement research runtime, scientific kernels, protected backtests, model providers, or learning systems.

Classify every execution:

- `EXPECTED_RED`: an application proposition fails because its production mechanism is intentionally absent.
- `HARNESS_GREEN`: generator, oracle, isolation, schema, or report works.
- `UNEXPECTED_GREEN`: an application proposition passes without justified behavior; investigate vacuity.
- `HARNESS_BUG`: verification infrastructure is incorrect.

Expected red must arise from its named missing mechanism, not import failure, malformed fixtures, or unrelated exceptions. Keep harness self-tests green.

## Review sequence

1. Use `seam-review` vocabulary to reconstruct composed mappings and authority/state effects without reopening local semantics.
2. Run `fundamentals-review` on every HIGH-risk composite and behavioral family, preserving its verdict discipline.
3. Run `grill-with-docs` against scripted autonomy, leaked labels, narrow scenarios, blanket conservatism, endless analysis, forced methodology, test-only paths, circular facts, and unnecessary LLM judges.
4. Reconcile only non-semantic defects. Classify required new product meaning as `ARCHITECTURE_GAP`.
5. Never mark experimental artifacts canonical or `LOCKED`.

## Completion standard

Use multidimensional metrics. Keep temporal leakage, unauthorized access, fabricated evidence, and invalid promotion as hard failures. Issue implementation `GO` only when HIGH-risk composites discriminate, behavioral families survive review, hidden truth is isolated, objective graders dominate, expected-red results are intentional, and no production code was added.

End by stating what the design and harness did not prove.
