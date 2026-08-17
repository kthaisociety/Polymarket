# Work packet: Polymarket boundary, volatility, and alternative-data loop

## Identity

- Packet: `polymarket.test-boundary-volatility-and-alternative-data`
- Owning architecture block: open-ended exploration, with conditional formalization/development.
- Semantic transition or responsibility: development-only sampled probability paths → authored
  boundary-aware features and falsifiers → retained candidate or rejection.
- Input repository state: `bdl-polymarket@626f0e74` on
  `codex/polymarket-time-series-research`.

## Objective

Determine whether logit-space state, boundary distance, realized volatility, volatility change, or
an exact legally sourced external series adds stable chronological predictive value beyond current
probability and raw-price path baselines; use the governed formalization/protected path only if a
candidate first survives development evidence.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, architecture
  map, sandbox authority, alignment policy, and the Polymarket/time-series/work-packet skills.
- Owning block and transition: exploration README/implementation and
  `sandbox.execute-analysis`.
- Relevant adjacent interfaces: exact retained corpus
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`,
  partition `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`,
  official-source scout/retain/register path, formalization, development, and protected governance.
- Explicit exclusions: protected values before freeze/permit, production writes, invented
  alternative data, unregistered web values in analysis, Kthais/engine changes, and calling sampled
  probabilities executable quotes.
- Assumptions: retained paths are hourly sampled YES-token probabilities with exact question/event
  identity; the final seven event groups/45 markets remain protected.

## Change boundary

- Permitted components: pure domain-neutral sandbox numeric primitives with adversarial tests;
  authored study sources/immutable receipts; one study report/ledger entry; exact public-source
  expansion only when a development hypothesis names a source and join; conditional formal objects
  only after the design skill and development gate are satisfied.
- Allowed state effects: local content-addressed public-source retention, development-only sandbox
  execution, repository evidence/docs, and one coherent local commit.
- Forbidden state effects: network/filesystem access from authored code, production database
  mutation, protected exposure without independent authority, silent candidate selection, or
  validated memory from development evidence.

## Correctness

- Governing invariants: I1-I6, I9, I12-I14, I17-I18, and I21-I26.
- Failure modes: undefined logit at 0/1; clipping that manufactures a boundary effect; volatility
  fitted across test folds; predicting magnitude and reporting direction; pooling event dependence;
  selecting an external series after seeing correlations; misaligned publication clocks; and
  pseudo-PnL without executable quotes.
- Expected output: exact source/receipt identities for raw versus logit dynamics, absorption/escape
  transitions, fold-legal volatility features, simple chronological models, and retained
  falsifiers. External data either has an exact need/source/availability/join or is recorded as not
  warranted.
- Violating counterexample: mutate every protected price/question/outcome; all development results
  remain unchanged. Attempt a host/interface call from authored code; authorization denies before
  data access.
- Required tests: pure numeric primitives work without widening imports/attributes/host access;
  domain errors remain structured failures; exact protected-isolation regression remains green;
  every authored attempt retains actual accesses and zero protected exposure.
- Integration evidence: every study source runs through `run_corpus_studies`; any surviving formal
  candidate uses harness-owned development evaluation and only then the protected-review skill.

## Completion evidence

- Frozen hypotheses and rivals precede result inspection.
- Numeric surface regression, focused adapter tests, complete Chronos gate, receipt/source hashes,
  and clean static checks pass.
- Study report distinguishes volatility prediction, directional prediction, boundary behavior,
  execution, and alternative-data limitations.
- Coherent Chronos changes are committed locally without push.

## Boundary revisions

1. The first requested logit analysis exposed that the sandbox lacked pure `log` and `exp` calls.
   The packet permits only those domain-neutral numeric primitives plus tests; no data or side-effect
   authority changes.
2. Formalizing an absolute-move candidate exposed a blanket prohibition on using one field as both
   legal predictor history and future outcome. The packet permits same-field autoregression because
   the evaluator still enforces `reference_time <= decision_time` for history and
   `decision_time < reference_time <= horizon_end` for the outcome path.
3. The same formalization exposed that `make_label` received the future path but not the already
   authorized decision-time histories needed to define a change. The packet permits those exact
   instrumented histories in label construction; it adds no field or time authority.
4. The first dimensioned formal run exposed positional comparison between schema-order observation
   dimensions and canonicalized `SampleKey` dimensions. The packet permits canonicalized named
   comparison in both development and protected authored replay.

## Completed evidence

- Diagnostics 01–03 ran through the development-only analysis harness with immutable source and
  receipts. Logit did not remove reversal; volatility predicted magnitude but failed the
  incremental time-to-close gate; all directional models failed delayed/cost controls.
- Formal trial 04 physically omitted protected markets, published two authority-issued authored
  candidates, and produced 84 chronological out-of-fold predictions with exact trial/evidence
  identities and actual program accesses.
- The realized-variance OLS candidate was rejected: MSE `0.00357062` versus `0.00194354` for the
  expanding-mean baseline.
- CME FedWatch was identified as the exact external probability source, but official access is
  credentialed/paid. FRED realized-rate series were rejected as semantically weaker substitutes.
- No protected backtest, production write, Kthais/engine change, push, merge, or PR occurred.
- Validated question memory remains unchanged because this is development evidence, while the
  repository study/receipt retains the negative result for future research context.
