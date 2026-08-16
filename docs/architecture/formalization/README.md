# Scientific Formalization

## First principle

**Exploration becomes science only through explicit, reproducible identity.**

Temporary analysis is free-form. Promotion captures exactly what a candidate means, depends on,
and changes. Material change creates lineage rather than mutating an identity in place.

```mermaid
flowchart TD
    ANALYSIS["Model-authored analysis"] --> FA["FeatureAnalysis evidence"]
    FA --> INTERPRET["Model interpretation"]
    INTERPRET -->|"formalization.create-candidate"| CAND["Candidate with ancestry"]
    INTERPRET -->|"feature.revise-from-diagnostics"| ANALYSIS
    CAND -->|"feature.define-identity"| FD["FeatureDefinition"]
    FD -->|"feature.compile-definition"| FX["FeatureExpression"]
    FD -->|"feature.materialize-definition"| FSERIES["FeatureSeries"]
    FD -->|"feature.assemble-set"| FSET["FeatureSet"]
    CAND -->|"model.define-recipe"| MODEL["ModelDefinition"]
    MODEL -->|"model.define-ensemble"| ENS["EnsembleDefinition"]
    FSET --> SYSTEM["PredictiveSystemDefinition"]
    MODEL --> SYSTEM
    ENS --> SYSTEM
    DATASETUP["DatasetSetup — proposed"] --> SYSTEM
    SYSTEM -->|"formalization.version-material-change"| VERSION["New version with lineage"]
```

The model owns the interpretation that turns diagnostic evidence into a proposal to retain, revise,
combine, formalize, or reject a candidate. The harness owns exact feature identity, temporal
legality, provenance, fitted-state boundaries, and version lineage. Feature analysis remains
evidence, not automatically a feature. Fitted transforms are learned state and must later fit inside
the legal training boundary.

- [Transition contracts](transitions/README.md)
- [Implementation map](IMPLEMENTATION.md)

Authoritative sources: Scientific kernel, architecture, I2, I3, I5, I6, and I13.
