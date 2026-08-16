# Mission and Environment

## First principle

**The model may explore uncertainty, but only the human can authorize the durable mission.**

Task compilation preserves breadth, uncertainty, constraints, and original intent. It does not
perform research. Subordinate questions may evolve autonomously; a genuine change to the main goal
returns to exact human confirmation.

```mermaid
flowchart TD
    M["UserMandate + environment metadata"]
    P["ResearchTaskProposal + exact readback"]
    H{"Human confirmation"}
    T["ResearchTask"]
    D["Proposed direction change"]
    A["Same-task agenda evolution"]
    V["New ResearchTask version"]

    M -->|"mission.confirm-task"| P
    P --> H
    H -->|"exact proposal"| T
    T --> D
    D -->|"mission.evolve-direction: goal preserved"| A
    D -->|"mission.evolve-direction: goal changed"| H
    H --> V
```

Authority changes only at human confirmation. Dataset contents, model calls, findings, and protected
evidence are outside this block.

- [Transition contracts](transitions/README.md)
- [Implementation map](IMPLEMENTATION.md)

Authoritative sources: Contract 001, locked task decisions, I10 and I24.
