# Mission implementation map

Status: **partial implementation**.

- Code: `src/research_agent/task_compilation.py`
- Contract tests: `tests/contract/test_task_compilation*.py`
- Transition contracts: [`transitions/`](transitions/)
- Known red: task-compilation failure behavior remains incomplete.

## Exact horizon implementation

`UserMandate`, `ResearchTaskProposal`, `ResearchTask`, runtime initialization, and `ContextPacket`
now transport one immutable `TemporalOffset`. It distinguishes absolute elapsed microseconds from
civil-calendar months/quarters. Calendar construction requires explicit exact-input anchoring,
month-end behavior, timezone identity, and DST/fold behavior; all fields participate in proposal
and task semantic identity and in the human readback.

API migration is intentionally explicit:

- `forecast_horizon_months: int | None` became `forecast_horizon: TemporalOffset | None`;
- prior elapsed callers use `TemporalOffset.elapsed(timedelta(...))`;
- calendar callers use `TemporalOffset.calendar(...)` with every policy supplied;
- integers are rejected rather than silently converted to calendar or elapsed time.

An unresolved horizon remains `None` and blocks target publication. No global month-end or timezone
convention was introduced because the mission contract assigns those scientific choices to the
confirmed task rather than infrastructure.

This file evolves with the implementation. Contract meaning changes only through architecture review.
