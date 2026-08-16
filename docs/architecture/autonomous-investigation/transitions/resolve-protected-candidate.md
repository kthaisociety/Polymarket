# `investigation.resolve-protected-candidate`

## Mapping

\[
f_{\text{investigation.resolve-protected-candidate}}:
(CredibleCandidate, DevelopmentEvidence, FrozenIdentity, Predeclaration)
\rightarrow ProtectedResolution
\]

```mermaid
flowchart LR
    INPUT["Issued credible candidate + evidence"] --> FROZEN["Issued exact frozen identity"]
    FROZEN --> PLAN["Authority-issued predevelopment plan"]
    PLAN --> GOV{"Independent governance"}
    GOV -->|"deny before content"| DENIED["DENIED resolution"]
    GOV -->|"permit"| VIEW["Exact protected view"]
    VIEW --> RUN["Same frozen authored source"]
    RUN --> REPORT["Independent EvaluationReport"]
    REPORT --> VALIDATE{"Independent Validator"}
    VALIDATE -->|"PROMOTE"| FINDING["ValidatedFinding"]
    VALIDATE -->|"REJECT"| NEGATIVE["NegativeResult"]
    FINDING --> OUTPUT["Issued AuthoredProtectedResolution"]
    NEGATIVE --> OUTPUT
```

## Contract

- The service resolves, rather than accepts from the researcher, governance authority, validation
  authority, protected scope binding, protected catalog, evaluation specification, promotion
  standard, and claim template.
- The executed source and scientific manifest are the exact frozen candidate selected by the
  issued development evidence.
- Protected exposure is recorded before content becomes available to execution.
- A denial carries no protected view, run, report, decision, finding, or negative-result reference.
- Exact idempotent replay returns the original resolution; changed semantics under the same key
  conflict.

## Failure modes exercised

- self-consistent frozen or plan substitution;
- caller-appointed governance/validation authority;
- protected binding or catalog substitution;
- future predictor poison;
- duplicate exposure or protected execution on retry;
- finding or rejection status supplied by the researcher.
