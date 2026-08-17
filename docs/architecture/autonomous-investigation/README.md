# Autonomous authored investigation

## First principle

The researcher authors the scientific method. The harness owns information access, temporal
legality, evidence identity, resource bounds, trial ancestry, and state-transition authority.

This block implements the missing semantic bridge between exploratory interpretation and the
existing deterministic formalization/development/protected machinery. It is explicitly not a
catalog of domain-specific analysis tools.

Repository-aware researchers may begin with one Polymarket scope router and then load the smallest
of three stage-specific, versioned guidance skills. The skills improve scientific judgment but
remain outside every authority boundary:

```mermaid
flowchart LR
    Q["Polymarket research mandate"] --> PS["start-polymarket-research"]
    PS --> AS["analyze-time-series-data"]
    AS --> AE["Exploratory evidence"]
    AE --> FS["design-time-series-feature-set"]
    FS --> C["Authored candidate proposal"]
    C --> DEV["Harness-owned temporal development"]
    DEV --> BG["review-backtest-gate"]
    BG --> REQ["Request or revise recommendation"]
    REQ --> GOV{"Independent freeze and governance"}
    AS -.->|"guidance only"| HARNESS["Existing information and provenance controls"]
    FS -.->|"guidance only"| HARNESS
    BG -.->|"never self-authorizes"| GOV
```

The skill instructions are deliberately malleable Markdown. Their outputs are analysis memos,
candidate proposals, and gate recommendations—not observations, definitions, permits, decisions,
findings, or memory records merely because an agent wrote them.

```mermaid
flowchart TD
    Q["ResearchQuestion"] --> CTX["Bounded ResearcherContext"]
    CTX --> SRC["Authored source + scientific manifest"]
    SRC --> PUB["CandidatePublisher"]
    PUB --> HIST["Legal histories at each decision time"]
    PUB --> PATH["Mature outcome paths"]
    HIST --> FEAT["make_features"]
    PATH --> LABEL["make_label"]
    FEAT --> FOLDS["Harness-owned temporal folds"]
    LABEL --> FOLDS
    FOLDS --> FIT["fit on training rows only"]
    FIT --> PRED["predict without outcomes"]
    PRED --> EVIDENCE["Out-of-fold evidence + actual accesses"]
    EVIDENCE --> RULE{"Predeclared stopping rule"}
    RULE -->|"revise"| CTX
    RULE -->|"budget exhausted"| NEG["Negative result"]
    RULE -->|"credible"| ELIGIBLE["Freeze-eligible candidate"]
    ELIGIBLE --> FREEZE{"Independent exact freeze"}
    FREEZE -->|"deny"| DENIAL["Recorded denial; question remains open"]
    FREEZE -->|"seal"| PROTECTED["Same authored source on protected data"]
    PROTECTED --> MEASURE["Independent Evaluator"]
    MEASURE --> VALIDATE{"Independent Validator"}
    VALIDATE -->|"promote"| FINDING["ValidatedFinding"]
    VALIDATE -->|"reject"| PREJECT["Protected NegativeResult"]
    FINDING --> MEMORY["Validated question memory"]
    PREJECT --> MEMORY
    MEMORY --> ARCHIVE["Crash-durable structured archive"]
    ARCHIVE --> INDEX["Generated Markdown + Mermaid research index"]
    MEMORY --> FUTURE["Bounded future context + explicit reopen policy"]
```

## Responsibilities

- accept a question, an exact authorized development catalog, sample population, and fixed budget;
- publish exact authored source, manifest, rationale, evidence refs, and trial ancestry;
- expose the universal exact-sample `history`, explicitly scoped `context_history`, `outcome_path`,
  `training_rows`, `model_state`, and `feature_values` interfaces inside phase-separated workers;
- construct temporal information and outcome boundaries outside authored code;
- return selection-exposed evidence for model interpretation and revision;
- preserve negative and failed trials rather than only the winner.
- resolve an exact frozen authored candidate through external protected-data, governance, and
  validation authorities;
- record only an issued protected finding or protected rejection as terminal question memory.

## Non-responsibilities

- it does not declare development evidence validated;
- it does not let the researcher authorize protected access, freeze, promotion, memory, or
  reporting; those decisions remain independently configured;
- it does not prove a scripted test researcher has good scientific judgment;
- it does not replace the optimized `FeatureExpression` substrate;
- it does not add a special action for geography, importance, interactions, or each model family.
- repository skill guidance is not automatically injected into standalone `ModelProvider` context;
  that requires an explicit, version-bound context-routing transition rather than an implicit file
  read.

See [IMPLEMENTATION.md](IMPLEMENTATION.md) and the locked
[autonomous investigation contract](../../specification/AUTONOMOUS_INVESTIGATION_CONTRACT.md).
The executable transition contracts are indexed under [transitions/](transitions/README.md).
