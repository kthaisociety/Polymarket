# XTracker post-count alternative-data study

Epistemic status: **ACTIVE DEVELOPMENT RESEARCH — PROTECTED DATA UNEXPOSED**.

This study audits and then conditionally tests the official public XTracker records for development
event `739241`, the nine Elon Musk post-count bracket contracts covering July 25 12:00 PM through
July 27 11:59:59 AM Eastern time in 2026.

The source is retained using the exact UTC API interval. `createdAt` is the post reference time and
the later `importedAt` is the conservative availability time. Post content is retained as part of
the immutable public response but excluded from every derived observation and feature.

The frozen source and research boundaries are in the
[work packet](../../docs/work-packets/polymarket-xtracker-alternative-data.md).

## Source and registration result

The passive scout issued one exact official candidate. Chronos retained its 18,391 response bytes
as `source:8027afa5c6b13a6ead8057e028070c6b2961ca357e8c75e936dc54dd7ebd561a`,
then derived and registered 59 post events. Reference times span 2026-07-25 17:31:24 UTC through
2026-07-27 15:38:01 UTC. Conservative import availability lags creation by at most 274.346 seconds.
No post content or metrics enter the derived dataset.

The real composition exposed one missing seam: the Polymarket development runner could not attach
an independently registered event field. The new `PolymarketRegisteredEventField` composition
accepts only the corpus environment and already-development `event_id` values; causal tests reject
protected and cross-environment observations before sandbox execution.

## Development results

Attempts 01 and 02 failed on explicit coverage assertions and are retained. Diagnostic 03 showed
why: the `115-139` contract has 8–10 hour gaps around the nominal six-hour decisions, while the
other eight contracts have legal windows in all six blocks. Attempt 04 preserved the declared
4.5–7.5 hour tolerance and excluded those six irregular rows rather than interpolating them.

The fixed augmented ridge failed decisively on the remaining 32 forward rows:

| Recipe | Observation / block-macro MSE | Blocks won vs augmented |
|---|---:|---:|
| No probability change | `0.008214` | 4/4 |
| Target path + static bracket ridge | `0.017979` | 4/4 |
| Plus imported count, pace, projection, and bracket gap | `0.040309` | — |

The external recipe lost to both controls in every test block and failed the predeclared gate. It
is rejected. This says the broad high-dimensional ridge is unusable on one event; it does not show
that correctly observed post counts are economically irrelevant. A future branch would need either
a much simpler structural mapping or multiple identical historical events before any general claim.

Protected events remain physically absent. Nothing was frozen or promoted.
