# DG-08-gap-deleted: Gap logs already deleted on the primary

**Severity:** Average

## Why it matters
FAL cannot ship logs that no longer exist: the standby needs them restored from backup, or an incremental roll-forward.

## Check
1. Item *Gap logs already deleted here*; `list backup of archivelog from sequence <n>` in RMAN.

## Fix
1. `restore archivelog from sequence <n>` on the primary or roll the standby forward (`recover standby database from service`).

## Escalate
Data Guard owner.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
