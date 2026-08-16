# Architecture Meta-Tests

Use these questions to challenge proposed abstractions, tools, state fields, gates, and fixes.

They are heuristics, not runtime tests.

## State

> Would knowing this materially change what a competent researcher should do next?

If no, but it is needed for audit/reproducibility, it likely belongs in trajectory/ledger/artifacts instead of `ResearcherState`.

## Resume

> If I froze the researcher right now, what would I need to know to resume the work intelligently?

## Context

> Would a competent researcher need this in working memory for the next decision?

## Human-limit check

> Are we omitting this because it is irrelevant, or only because a human could not process it?

If the latter, preserve machine access through retrieval/synthesis.

## Tool

> Does this provide a deep reusable research capability, or is it redundant with open-ended Python analysis?

## Gate

> What concrete failure mode does this gate prevent?

If no meaningful answer exists, question the gate.

## Abstraction

> What breaks if this abstraction does not exist?

If only naming/style becomes less elegant, the abstraction may be premature.

## Observation

> What does the researcher need back to make the next decision correctly?

## Semantic commit

> Would a competent researcher update their durable notebook/mental model now, or are they still gathering evidence?

Second check:

> If resumed tomorrow from this state, would this update help continue correctly?

## Memory

> Is this durable knowledge that should change future research behavior?

If not, keep it as evidence/history rather than cross-task memory.

## Evidence vs interpretation

> Is this a fact produced by computation, or the agent's interpretation of that fact?

Keep both, but do not conflate them.

## Promotion

> Has the evidentiary burden increased enough to justify the higher epistemic status?

## Domain specialization

> Is this fundamentally different scientific machinery, or the same kernel asked a different question over different data?

## Failure recovery

> Would this recovery preserve the meaning of the experiment currently being evaluated?

If no, create a new scientific version/candidate.

## Blocking failure

> If this operation failed, could a competent researcher mistakenly continue as if it succeeded?

If yes, make failure explicit and downstream-blocking.

## Context reconstruction

> If the LLM context vanished completely, could the system rebuild a scientifically equivalent working context from durable state + active research episode/checkpoint + referenced evidence?

## Reporting

> If wording/layout changes, should the scientific conclusion change?

If yes, the information belongs in `ValidatedFinding`/evidence rather than presentation.

## Provider boundary

> If the model provider changed tomorrow, which scientific modules would have to be rewritten?

The desired answer is: provider integration/runtime adapter, not the research/scientific architecture.

## Planning depth

> If Codex chooses the wrong implementation detail here, is the consequence a cheap local refactor or a plausible-looking scientific error?

Cheap refactor → let implementation discover it.

Scientific/governance corruption → specify/test before implementation.
