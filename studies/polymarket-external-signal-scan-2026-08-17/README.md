# Polymarket XTracker post-count mechanism scan

Epistemic status: **EXPLORATORY DEVELOPMENT REJECTION — PROTECTED DATA UNEXPOSED**.

This study began with a value-free inventory of 24 retained development events/155 markets and
selected the repeated post-count bracket family before reading its probability paths. Eight exact
official XTracker responses were acquired and retained without credentials. Per-post `importedAt`,
not platform creation time, governed historical availability. Post content and engagement metrics
were excluded.

The exact selection, revisions, gates, and exclusions are retained in the
[work packet](../../docs/work-packets/polymarket-external-signal-candidate-scan.md). Receipts contain
the snapshot, partition, source hashes, registered temporal identities, actual field accesses, and
the explicit `protected_values_exposed=false` assertion.

## Results

1. Source 01 found 11 development post-count events spanning eight users. Five users fit the
   original bounded per-post transform; larger Elon, White House, and Trump responses did not.
2. Source 02 proved that final registered counts mapped to exactly one winning bracket in all five
   available events. The hard-elimination hypothesis had zero eligible rows because each event's
   final count remained in its lowest listed bracket. It was rejected without changing the gate.
3. Source 03 tested two fixed Poisson posting-rate forecasts at days 1-5 over 240 next-day rows.
   Both were materially worse than the current sampled probability and won zero of five events:
   elapsed-rate observation MSE `0.01642`, trailing-rate MSE `0.02124`, current-probability baseline
   MSE `0.00710`. Neither probability model advanced.
4. The elapsed-rate recipe showed a selection-exposed directional pattern on those five events:
   102 two-cent discrepancies, mean one-cent-screened next-day change `+0.01674`, 66.7% positive,
   and positive event means in four of five events. The rule was frozen before evaluating the three
   previously transform-blocked same-week events.
5. Compact decision-count temporal datasets eliminated the concrete transform bottleneck without
   weakening authority: each observation is the cumulative count of exact retained records with
   `importedAt <= decision`. On untouched events `716159`, `716151`, and `716152`, source 04 produced
   76 signals but mean one-cent-screened change was `-0.01382`, only 46.1% were positive, and all
   three event means were negative. The apparent directional lead failed confirmation decisively.

## Retained exact external datasets

- Discovery per-post datasets: CZ `derived:6d9231f2…`, Zelenskyy `derived:f443cc3d…`, NYC Mayor
  `derived:a7fc391e…`, Khamenei `derived:482656e1…`, Ted Cruz `derived:d997c7c2…`.
- Confirmation decision-count datasets: Elon `derived:43c914d6…`, White House
  `derived:fa478ad6…`, Trump Truth Social `derived:e66279b4…`.
- The compact derivation source SHA-256 is
  `d94aefe644f07529f2d6e7782c68f8cc8e91e5fed96edc62be82d3e1db71a4e4`.

Historical probability samples are beliefs, not executable bid/ask quotes. The one-cent screen is a
falsifier rather than a profit estimate. No candidate was formalized, no freeze was issued, no
protected request was made, and terminal question memory was correctly not updated: that authority
exists only after a governed protected resolution. The durable negative evidence is the immutable
source/receipt chain and this exploratory ledger entry.
