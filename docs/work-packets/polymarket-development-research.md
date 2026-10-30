# Work packet: Polymarket development research

## Packet identity

- Packet: `polymarket.run-event-grouped-development-research`
- Owning blocks: exploration, formalization, and development.
- Input state: `historical checkpoint c6b20c70` on `codex/polymarket-time-series-research`.

## Objective

Use the exact retained production corpus to run researcher-authored exploratory programs over a
development-only capability, compare several mechanism-driven hypotheses with the sampled market
probability baseline, and carry only defensible candidates into temporal development evaluation.

## Context boundary

- Loaded global authority, the Polymarket startup and analysis skills, feature-design principles,
  and the exploration/development transition contracts.
- Exact source corpus:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Explicitly excluded until a separate gate passes: protected values, protected metrics, promotion,
  reporting, cross-task learning, production writes, external-system changes, and trading claims.

## Research design

- The prediction question is whether an outcome-token settles at one, using only sampled prices
  observed by a declared decision point in that market's retained path.
- Whole server `event_id` groups are ordered by their latest recorded resolution time. The final
  chronological event block is protected; earlier groups are development. Related markets never
  cross that boundary.
- Exploration starts with one decision per market at a fixed observation ordinal. This avoids using
  the later close or resolution to choose the decision timestamp. Coverage conditioning and the
  variable economic horizon remain explicit limitations.
- The first trial budget is four families: calibration, price-path momentum/reversal, path
  variability/staleness, and decision-ordinal sensitivity. Each must compare with the current-price
  probability baseline and report event concentration or instability where measurable.
- A hypothesis is rejected or revised when it is baseline-inferior, concentrated in a few events,
  unstable across decision ordinals/time blocks, or disappears after conditioning on current price.

## Change boundary

- Permitted: a corpus-to-development capability composer, a public offline study command, authored
  study sources/receipts, focused tests, formal candidate/development composition only if exploration
  warrants it, and active Chronos documentation/memory needed by the resulting transition.
- Forbidden: database access in authored code, filesystem/network/process capabilities in authored
  code, any protected event value in an exploratory view or receipt, tuning on protected output,
  and modifications outside this repository.

## Correctness and adversaries

- Changing a protected event's prices, payout, question, or lifecycle must not change any
  development view value or exploratory result.
- Requesting a protected-only field or unknown view must be denied before value disclosure.
- Partition identity, source hash, exact snapshot ref, actual field accesses, resource limits, and
  result status must be retained.
- The command must fail closed for an unknown/corrupt snapshot, empty source set, partition too
  small for both scopes, non-succeeded authored execution, or a conflicting receipt path.

## Completion evidence

- Focused causal tests and the complete Chronos gate pass.
- At least four exact authored sources execute through `AnalysisHarness` against the development
  capability and produce immutable receipts with no protected values.
- Findings name the baseline, sample/event counts, limitations, and retain/revise/reject decision.
- Any later protected request cites a frozen system and separate eligibility evidence; otherwise the
  packet closes as a retained development negative without consuming protected data.

## Boundary revisions

- Trial 06 showed that a successful result larger than the generic inline preview could remain only
  in an in-memory artifact and disappear when the offline command exited. The permitted command
  seam was revised to retain up to a bounded 200 KB structured detail and fail closed when a
  successful receipt would otherwise contain no detail. The failed receipt remains in history and
  trial 07 is a new source/receipt.

## Transition receipt

### Result

- Status: **COMPLETE — DEVELOPMENT REJECTION**.
- Exact partition:
  `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
- Development scope: 24 event groups and 155 markets.
- Protected scope: 7 event groups and 45 markets; no value exposed and no protected request made.

### Evidence and disposition

- Seven exact authored trials ran through `AnalysisHarness`; sources, code hashes, actual field
  accesses, results, warnings, corpus identity, and partition identity are retained under
  `studies/polymarket-resolution-research-2026-08-17/`.
- The raw 24th-sample probability achieved development Brier 0.1037 versus a descriptive
  same-sample prevalence comparator of 0.1171.
- Every tested momentum strength worsened Brier. Fold-local scalar and affine calibration worsened
  market-weighted Brier in all three expanding whole-event folds.
- Rolling one-event-ahead scalar calibration improved equal-event Brier only from 0.1224 to 0.1181,
  won 6 of 16 events, and was concentrated; market-weighted Brier worsened from 0.0824 to 0.0893.
- No authored adjustment met the predeclared baseline, stability, and concentration criteria. No
  feature/system definition, freeze, protected evaluation, finding, or promotion was created.

### Memory status

- The development rejection is indexed in the repository exploratory research ledger with exact
  receipts. Validated terminal question memory is unchanged because Chronos reserves that authority
  for independently issued protected findings or protected rejections.
- A future question may cite this study and exact partition, but it may not silently reinterpret the
  development rejection as a `NegativeResult` or inspect the held-out events before a new frozen
  system earns a protected permit.
