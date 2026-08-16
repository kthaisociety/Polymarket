# Automated seam-specification experiment

Status: **experimental — candidate contracts are not canonical architecture**

This directory contains an automated review pass over the architectural seams registered in `docs/specification/SEAM_REGISTER.md`. It begins at action.authorize-request. The manually reviewed mission.confirm-task–action.decode-intent contracts remain canonical and are used only for read-only calibration.

## Review loop

Each seam is processed as:

```text
seam-review DISCUSS
  -> provisional contract
  -> fundamentals-review
  -> grill-with-docs adversarial challenge
  -> non-semantic reconciliation
  -> candidate classification
```

The reviewer may reconcile only consequences already fixed by locked architecture. Genuine choices about scientific meaning, authority, state, evidence, time, identity, failure, lifecycle, or the exploration/formalization boundary are preserved for human arbitration.

## Candidate classifications

- `CANDIDATE_CONSENSUS`
- `USER_DECISION_REQUIRED`
- `ARCHITECTURE_CONFLICT`
- `INSUFFICIENT_SPECIFICATION`
- `TEST_INSUFFICIENT`

No candidate is `LOCKED`. Nothing in this experiment authorizes production code, executable application tests, canonical contract replacement, or seam-register mutation.

## Layout

- `calibration/` — comparison against manually reviewed mission.confirm-task–action.decode-intent.
- `milestone-*` — candidate contracts grouped by the register's milestone names.
- `study-cards/` — concise human comprehension cards.
- `REVIEW_QUEUE.md` — ranked human-review queue.
- `SUMMARY.md` — aggregate classifications and concerns.
