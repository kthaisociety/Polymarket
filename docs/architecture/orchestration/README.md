# Codex One-Shot Orchestration

## First principle

**Agents may build in parallel; objective evidence, not agent confidence, controls integration.**

This block builds the product but is not part of the product's scientific runtime.

```mermaid
flowchart TD
    HUMAN["Human-approved mission and limits"] --> ROOT["Root orchestrator"]
    ROOT --> DAG["Dependency graph"]
    DAG --> WP1["Bounded implementation package"]
    DAG --> WP2["Independent test package"]
    DAG --> WP3["Architecture review package"]
    WP1 --> INTEGRATE["Root-controlled integration"]
    WP2 --> INTEGRATE
    WP3 --> INTEGRATE
    INTEGRATE --> GATE{"Contract + adversarial + composite gate"}
    GATE -->|"green"| NEXT["Next dependency wave"]
    NEXT --> DAG
    GATE -->|"repairable"| REPAIR["Targeted repair package"]
    REPAIR --> INTEGRATE
    GATE -->|"true architecture conflict"| HUMAN
    GATE -->|"all completion evidence"| DONE["Verified one-shot completion"]
```

Work packages own semantic transitions and explicit files, not vague milestones. A package declares
inputs, outputs, upstream contracts, invariants, forbidden changes, tests, evidence, and stopping
conditions. Shared mutable state and cross-block transitions remain root-controlled.

- [Transition contracts](transitions/README.md)
- [Implementation map](IMPLEMENTATION.md)

This block requires a separate review before it becomes an executable one-shot protocol.
