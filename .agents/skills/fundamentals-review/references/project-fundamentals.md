# Insurance project fundamentals

Use this as a routing map, not a substitute for the authoritative repository sources. Follow the cited source when a principle governs the seam under review.

## Authority and language

- Architecture drives tests and implementation; code does not redefine architecture. Follow the precedence and contradiction protocol in `docs/specification/ALIGNMENT_AND_DIAGRAMS.md` sections 3–5 and the hierarchy in `AGENTS.md`.
- `CONTEXT.md` owns canonical domain terms and links each term to its detailed authoritative home. Do not create near-synonyms for convenience.
- Locked decisions, invariants, and approved contracts are authority. Missing low-level mechanics remain implementation choices unless a concrete semantic failure makes them architectural.

## Scientific identity and time

- Knowledge at simulated time `t` admits only observations with `available_at <= t`; `reference_time` alone is insufficient (`INVARIANTS.md` I1; `SCIENTIFIC_KERNEL.md` A1).
- Learned state is information and must obey its training boundary; prediction does not learn (`INVARIANTS.md` I2–I3).
- Predictor availability `I_t` and target maturity `S_t` are separate boundaries (`INVARIANTS.md` I23, I26).
- Protected evaluation requires a frozen, immutable scientific identity. Meaning-changing repair creates a new version and formal failure cannot silently become success (`INVARIANTS.md` I4–I6, I17).
- Development and protected evidence have different epistemic status; protected exposure is irreversible history (`INVARIANTS.md` I7, I22).

## Research freedom and authority

- The agent generates hypotheses; deterministic infrastructure decides whether they survive (`DECISIONS.md`, Core scientific principle).
- Constrain information and side effects, not intellectual or computational creativity (`ALIGNMENT_AND_DIAGRAMS.md`, Stable project principles).
- Use a few deep capabilities, including open-ended exploratory analysis. Freedom decreases and evidentiary burden increases from exploration through formalization to protected evaluation and promotion (`DECISIONS.md`, Action/tool space and Escalating epistemic gates).
- Exploratory code is encouraged, but sandbox policy controls authorized data, filesystem/process/network effects, secrets, protected data, and privileged stores (`INVARIANTS.md` I18; `AUTHORITY_SANDBOX_AND_TOOLS.md`).
- The beneficiary of a privileged decision may request but cannot self-authorize it (`INVARIANTS.md` I8).

## State, context, evidence, and loops

- `Trajectory`, `ResearchEpisode`, `ResearcherState`, and model context are distinct. A tool result is not a durable belief; committed state changes only at semantic commit boundaries (`INVARIANTS.md` I9; `DECISIONS.md`, State/context architecture).
- Research is looped, not a false linear pipeline. Scientific observations may update the active episode, but protected evidence cannot become an ordinary tuning signal (`DECISIONS.md`, Research loops).
- Context is selective working memory built over broader accessible knowledge. Compression changes accessibility, not evidence existence; explicit references must remain permission-safe and drillable (`INVARIANTS.md` I14–I16; `DECISIONS.md`, Context/knowledge).
- Evidence records are immutable/append-only, rejected evidence remains history, and claims retain provenance (`INVARIANTS.md` I11–I13).
- Environment, data, and schema identity must remain explicit so later changes do not rewrite historical meaning (`INVARIANTS.md` I24).

## Runtime and failure

- The research harness owns the autonomous loop; the model provider is replaceable and its transcript is not scientific memory (`INVARIANTS.md` I20; `DECISIONS.md`, Model provider/runtime).
- Retries must not duplicate irreversible effects (`INVARIANTS.md` I25).
- Exploratory operational failure is recoverable, formal scientific failure is explicit, and governance denial is hard. Formal fallback is forbidden unless predeclared (`DECISIONS.md`, Failure semantics).
- A structured observation must carry decision-relevant numerical and epistemic context plus authorized drill-down, not merely success or massive stdout (`DECISIONS.md`, Structured observations).

## Test standard

- Tests are architectural evidence. A critical seam needs an observable consequence, explicit failure cases, and a falsifying test aimed at a plausible false-success implementation (`DECISIONS.md`, Test philosophy; `docs/specification/TEST_STRATEGY.md`).
- Sequence is not causality. If the proposition is that information affects behavior, vary only that information and prevent side-channel access.
- For HIGH-risk seams, name a violating mutation and ensure the proposed test becomes red. Do not weaken architecture to satisfy an existing test (`AGENTS.md`; `docs/specification/ALIGNMENT_AND_DIAGRAMS.md`).
- Keep local seam proof separate from composite-loop proof, and label agent evidence according to what it actually demonstrates.

## Complexity discipline

- Complexity must be earned by a concrete failure mode. Do not require framework structure, storage layout, or narrow tool taxonomies when behavioral constraints suffice (`AGENTS.md`; `DECISIONS.md`, Architecture / implementation strategy).
