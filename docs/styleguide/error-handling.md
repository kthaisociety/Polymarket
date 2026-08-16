# Error handling

> General conventions for making failures explicit, observable, and contained.

## Classify the failure before choosing the mechanism

Use the mechanism that matches the kind of failure:

| Situation | Expected treatment |
|---|---|
| Invalid startup configuration | Fail startup clearly |
| Expected outcome the caller must handle | Return an explicit typed outcome |
| Transient external failure | Retry only when safe, with a bound |
| Unsafe state | Stop the affected work and surface the condition |
| Unexpected programming error | Preserve context and contain it at the owning boundary |
| Cancellation or shutdown signal | Propagate it through the normal shutdown path |

The architecture documents define the concrete result types and lifecycle transitions. The style
guide does not mandate a particular result wrapper.

## Expected failures are part of the contract

If the immediate caller is expected to branch on an outcome, make that outcome explicit in the
function's return contract. Do not hide routine control flow inside broad exceptions.

Use exceptions for exceptional failures, contract misuse, or startup failure according to the
project's chosen architecture. Do not use them as an undocumented alternate return type.

## Fail fast during startup

Configuration, dependency wiring, and schema validation should fail before the application starts
doing work. A partially initialized process is harder to reason about than one that refuses to
start.

Keep startup failure at an obvious composition or entrypoint boundary. Library and domain code
should not terminate the process directly.

## Contain long-running work at its owner

A long-running loop or task needs one owning boundary that prevents an unexpected exception from
silently killing background work. That boundary must record the failure with enough context to
diagnose it and then follow the architecture's recovery, halt, or shutdown policy.

Do not scatter broad catches throughout ordinary code. Catch the narrowest exception you can handle.
Catch `Exception`, not `BaseException`, at a deliberate last-resort boundary so cancellation and
process-level signals retain their intended behavior.

## Never swallow failures silently

An intentionally ignored exception must be narrow, documented by the surrounding operation, and safe
to discard. Prefer a construct such as `contextlib.suppress(SpecificError)` for expected cleanup
races. Never suppress `Exception`.

## Retries are bounded and observable

Retry only operations that are safe to repeat. Bound attempts or elapsed time, use backoff where
appropriate, and surface exhaustion as an explicit failure. Preserve the original cause so the final
observation explains what actually failed.

## Preserve context

When translating a dependency error into a project-level error, retain the original cause and add
domain context. Avoid leaking credentials, private data, or oversized payloads into logs.
