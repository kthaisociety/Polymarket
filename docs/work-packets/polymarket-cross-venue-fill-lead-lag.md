# Work packet: cross-venue fill lead-lag scout

## Identity

- Packet: `polymarket-cross-venue-fill-lead-lag`
- Owning architecture block: open-ended exploration
- Semantic transition or responsibility: exact retained two-venue taker-print bytes into a
  deterministic source-time H2 analysis artifact and exploratory memo
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the active
  low-latency program working-tree deltas; pre-existing external-data artifacts remain user-owned

## Objective

Determine whether same-aggressor one-cent-or-larger print innovations on either venue are followed
by aligned same-aggressor print changes on the matched venue over fixed 30-second, 2-minute, and
10-minute source-event-time horizons, with explicit coverage, freshness, cooldown, reverse-window,
pair, source-venue, and calendar-subperiod diagnostics.

## Context boundary

- Global authority loaded: repository/Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, alignment policy, style guide, and the time-series analysis principles
- Owning block and transition contract: exploration `README.md`, `IMPLEMENTATION.md`,
  `sandbox.execute-analysis`, and `artifact.persist-analysis-output`
- Relevant adjacent interfaces: exact Brazil semantic audit, retained cross-venue taker-fill
  artifact, low-latency hypothesis memo, and prior transaction-direction reversal failure
- Explicitly excluded work: quote or midpoint inference, collector `available_at` reconstruction,
  executable signals, fee/PnL/fill simulation, feature formalization, model fitting, threshold
  optimization, protected access, promotion, and durable memory
- Assumptions: fill `side` is the aggressor's YES-outcome side; `fill_time` is source reference time
  only and grants no historical decision-time availability

## Change boundary

- Permitted files or components: this packet/receipt, one authored script and immutable result/memo
  in the active external-data study, focused regression tests, study navigation, and the exploration
  implementation map
- Allowed state effects: read and hash retained local inputs; create deterministic local study
  artifacts under the existing study directory
- Forbidden state effects: database/network access, input mutation, production writes, protected
  values, hidden imputation, nearest/future joins described as legal information, or scientific
  promotion

## Correctness

- Governing invariants and decisions: I1, I11-I13, I17-I18, I24; `(value, reference_time,
  available_at)` remains distinct; exploration is provisional
- Concrete failure modes: mix Lula and Flavio; mix YES BUY/SELL transaction paths and rediscover
  bounce; use a future matched-venue print as the pre-trigger baseline; treat no print as zero
  movement; overlap every fragmented print; hide sparse matched updates; select horizons or freshness
  after seeing response values; call source ordering causal or executable
- Expected inputs and outputs: exact audit/tape hashes plus fixed parameters produce one canonical
  JSON result containing input/schema checks, accessed fields, counts/missingness, interarrival
  coverage, conditional aligned responses, reverse-window controls, pair/source/month slices, and
  explicit limitations
- Violating mutation or counterexample: replace the same-side baseline with the last any-side trade;
  a synthetic side-switch fixture must create a false response and turn the regression red
- Required local tests/evals: input hash/schema/mapping rejection; same-side isolation; no-future
  baseline; missing-response exclusion; max-horizon cooldown; deterministic output
- Required integration evidence: exact script run over the retained 59,000-row corpus with output
  hashes and a human-readable exploratory memo

## Completion evidence

- Focused authored-analysis tests pass
- Exact retained run completes and input/output/code hashes are recorded
- Memo reports coverage, missingness, direct observations, rivals, failed checks, and next falsifier
- Existing Polymarket adapter tests, Ruff/formatter, basedpyright, and `git diff --check` remain green
- Transition receipt states what source-time print analysis cannot prove

## Boundary revisions

1. The first exact run found all 4,713 retained Kalshi rows have `side = BUY`. Engine inspection
   established that Kalshi normalization stores the taker's selected outcome leg and the acquisition
   query retained only `outcome_index = 0`; NO-taking trades needed for the opposite YES direction
   never entered the artifact. The packet contracts to one-sided same-leg BUY-path diagnostics and
   must report raw versus response-eligible triggers. Symmetric H2 inference is forbidden until a
   successor acquisition retains both Kalshi outcome legs and canonicalizes them onto one YES-price
   convention.

## Execution receipt

- Exact input audit SHA-256:
  `75ec8496452816964f4db6749c1ba90db0c3bd1c27a5e0b510ef2a9e66d67d89`
- Exact 59,000-row compressed tape SHA-256:
  `7a08c71c2e88563a247dd10d9a5480a435dc6b834fbed168907a041bf0ffb32c`
- Authored analysis SHA-256:
  `8d61a4351d202b89e37dd3e23cd699f93b2f1f57326baee3dedad2204f3ec9b8`
- Canonical result SHA-256:
  `c082c7fcfa0e2cc25e15b5d4df3c363d55df0e0bd127fc2a17ced7dac73aea90`
- Determinism: an independent exact rerun reproduced the result byte for byte.
- Focused regressions: five passed, including future-baseline, side-switch, missing-response,
  missing-Kalshi-side, and input-authority adversaries.
- Verification: 91 Polymarket adapter tests passed; 460 broader Chronos tests passed with the two
  sandbox-prohibited local HTTP-server modules excluded; scoped Ruff and formatter checks passed;
  configured strict basedpyright passed with zero errors; `git diff --check` passed.
- Empirical disposition: **exploratory source-time print diagnostic — do not advance**. The
  one-sided eligible Kalshi-to-Polymarket path has a +0.220-cent conditional mean at 30 seconds but
  an effectively zero median, 14.8% response coverage, candidate/month instability, and a negative
  matched post-minus-reverse comparison. Polymarket-to-Kalshi coverage is 0.3% at 30 seconds.
- Transition boundary: no strategy, causal lead, executable quote, cost, PnL, or protected claim;
  symmetric H2 requires a successor dual-clock L2 corpus with both Kalshi outcome legs.
