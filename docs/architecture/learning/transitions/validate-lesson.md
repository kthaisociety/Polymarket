# learning.validate-lesson — CandidateLesson + independent evidence/authority → lesson validation decision

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Prevent a lesson or benefiting agent from self-promoting unsupported cross-task learning.

## Relevant locked invariants

I8, I13, I21–I22; slow-learning authority.

## Source A

Exact candidate lesson, predeclared validation standard, registry-issued independent validator
capability, canonical independent evidence/tasks, provenance/scope/currentness.

## Destination B

Immutable PROMOTE/REJECT lesson decision with reasons, exact scope/evidence/authority and no lesson mutation.

## Mapping f

Verify exact issued validator capability, requester/source/task/evidence independence, closed
affirmative evidence status, generalization/currentness and environment/task/subject scope; apply standard; decide.

## Must preserve

Lesson/type/scope, candidate and independent evidence periods/tasks, caveats, standard/version, validator.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Self-approval, same evidence used as independent, protected leakage, post-hoc standard, scope widening, content rewrite.

## Authority boundary

Independent lesson validator decides; candidate/reflector cannot.

## Allowed state mutation

Decision/ledger record.

## Forbidden state mutation

No candidate/source/memory/skill mutation.

## Failure semantics

Insufficient/non-independent/conflicting evidence rejects/blocks; no favorable default.

## Observable consequences

Candidate supported only by originating task rejects when standard requires cross-task evidence; independent support may promote.

## False-success implementations considered

Count reflection citations as validation; agent validates own lesson.

## Falsifying tests

Beneficiary/self-validator and evidence-overlap fixtures; scope/caveat equality. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Treat original reflection evidence as independent validation.

**Expected failure:** Overlap test red.

## Composite dependencies

learning.propose-lesson; learning.promote-lesson/ledger.record-rejected-lesson.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added evidence-independence and no-scope-widening.

## Remaining user decisions

None; validation standard is predeclared input.
