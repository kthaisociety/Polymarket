# Functions

> General convention: keep control flow shallow and keep orchestration readable.

## Keep nesting shallow

Aim for no more than three levels of nested control flow in a function. When the real work becomes
buried, extract a helper named for the operation or decision it owns.

```python
async def run_episode() -> None:
    while has_budget():
        action = await choose_action()
        observation = await execute_action(action)
        record_observation(observation)
        if should_stop(observation):
            return
```

A helper should represent a meaningful concept, not merely move lines elsewhere.

## Keep callers at one altitude

A top-level caller should read as orchestration: what happens and in what order. Push detailed
formatting, logging, metrics, persistence bookkeeping, and conversion into helpers or collaborators
that own those responsibilities.

## Make side effects visible

A function name and signature should make important side effects apparent. Prefer returning a value
over mutating hidden global state. Pass clocks, storage, providers, and other external collaborators
through explicit boundaries.

## Keep interfaces small

Expose the smallest stable operation that hides the implementation complexity callers do not need.
Do not split a cohesive operation into many public steps merely to make internal work visible.
