# Validated Cross-Task Learning

## First principle

**Past experience changes future behavior only after independent validation.**

```mermaid
flowchart TD
    HISTORY["Trajectory + ResearchLedger"] -->|"learning.reflect-history"| REFLECT["Reflection"]
    REFLECT -->|"learning.propose-lesson"| CAND["CandidateLesson"]
    CAND -->|"learning.validate-lesson"| VALID{"Independent decision"}
    VALID -->|"promote"| LEARN["Validated Memory or Skill"]
    VALID -->|"reject"| REJECT["Preserved rejected lesson"]
    LEARN -->|"learning.publish-to-knowledge"| KE["KnowledgeEnvironment"]
    KE -->|"learning.influence-future-research"| FUTURE["Scoped future context and behavior"]
```

The actor benefiting from a lesson cannot approve it. Scope and provenance travel with promoted
learning; publication does not make a lesson universally applicable.

- [Transition contracts](transitions/README.md)
- [Implementation map](IMPLEMENTATION.md)

Authoritative sources: State/context/memory specification, I8, I12, I13, I15, and I16.
