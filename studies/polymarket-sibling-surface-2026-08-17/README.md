# Same-event sibling probability-surface study

Epistemic status: **DEVELOPMENT CANDIDATE — FORMAL REPLAY PENDING — PROTECTED DATA UNEXPOSED**.

This study asks whether time-legal state and motion in other contracts sharing the server-recorded
Polymarket `event_id` improves six-hour forecasts beyond a target contract's own path. It makes no
claim that sibling contracts form an exhaustive or mutually exclusive outcome set.

The frozen design and gates are in the
[work packet](../../docs/work-packets/polymarket-sibling-surface-search.md).

## Retained results

The first authored source failed before analysis because its six-hour alignment helper indexed a
sentinel ordinal. The failed source and receipt are retained. The alignment-safe rerun used 8,647
legal samples from 22 development events and produced 7,779 test rows over 15 chronological test
events.

- Signed six-hour change failed: the augmented model beat the target-only model, but not the
  no-change control, and worsened in the early half.
- Fixed two-cent large-move incidence failed: the augmented model was worse than target-only
  overall and in the early half.
- Absolute six-hour change passed: augmented observation MSE was `0.00169977` versus `0.00202114`
  target-only and `0.00227059` naive; event-macro MSE was `0.00251662` versus `0.00267723` and
  `0.00325868`. It improved both chronological halves and won 9 of 15 events.

The predeclared compression trial selected the 14-feature static sibling-state recipe. Its
observation MSE was `0.00154980`, event-macro MSE `0.00242154`, early/late MSE
`0.00211257`/`0.00269190`, and it beat target-only on 11 of 15 events. Sibling-motion features alone
failed, so they are not carried forward. These are development findings, not protected or deployable
performance claims.

## Exact evidence

- Benchmark source SHA-256:
  `72577dc88539e23b67460007e4b07eb8cf5c45225ddeadbeb8137f302f077597`
- Compression source SHA-256:
  `3770e4e3cff457320ba8b52822b98dd232ca3a22a3f6530bca25003520204159`
- Receipts are retained under `development-receipts/`; all report
  `protected_values_exposed=false`.
