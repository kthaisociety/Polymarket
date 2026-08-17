# Same-event sibling probability-surface study

Epistemic status: **FORMAL DEVELOPMENT REJECTION — PROTECTED DATA UNEXPOSED**.

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

## Formal replay

Formal attempt 04 retained 305 exact keys but failed before candidate scoring because fewer than the
required 200 label-matured OOF predictions remained. Coverage-safe attempt 05 completed both model
evaluations over 457 keys, then failed while its receipt diagnostic requested an absent sample
dimension. Both failures and their exact sources are retained; no transient metric was reconstructed.

Reporting-safe attempt 06 changed only event ordering in the receipt diagnostic. The candidate
source strings and 457 keys were unchanged from attempt 05. The governed evaluator produced 413 OOF
predictions over 20 event groups:

- target-only ridge MSE: `0.00601997`; event-macro MSE: `0.00883438`;
- sibling-state ridge MSE: `0.00605519`; event-macro MSE: `0.00892503`;
- MSE delta versus target-only: `+0.00003523` (worse);
- early event-macro MSE: `0.00347287` versus `0.00333736` target-only;
- late event-macro MSE: `0.01437718` versus `0.01433139` target-only;
- event wins: 8 of 20; largest positive-improvement share: `0.37736`.

The candidate failed the fixed absolute MSE, aggregate improvement, both-half, and 60%-event-win
gates. The exploratory whole-event result therefore did not survive the authored expanding,
label-matured replay. This exact branch is rejected. It is not freeze-eligible, and no protected
backtest was requested or run.

## Exact evidence

- Benchmark source SHA-256:
  `72577dc88539e23b67460007e4b07eb8cf5c45225ddeadbeb8137f302f077597`
- Compression source SHA-256:
  `3770e4e3cff457320ba8b52822b98dd232ca3a22a3f6530bca25003520204159`
- Final formal driver SHA-256:
  `d0d54574f0c28b6f89d39d698c4e9f5aa3da9a77877ca305d36bc82b5bcc0b30`
- Final formal receipt SHA-256:
  `31ed5ccbbb5d00cfa66370c8261dbf97ddf5148ea1dc72ac497546f7c3a3d751`
- Receipts are retained under `development-receipts/`; all report
  `protected_values_exposed=false`.
