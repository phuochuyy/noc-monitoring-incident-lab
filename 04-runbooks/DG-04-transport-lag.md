# DG-04-transport-lag: Standby transport lag > 60 s

**Severity:** Warning

## Why it matters
Redo is not reaching the standby: the data-loss window grows (ASYNC).

## Check
1. Primary: `select dest_id, status, error from v$archive_dest where target = 'STANDBY'`.
1. Network between regions; standby listener.

## Fix
1. Fix the error shown in V$ARCHIVE_DEST; `alter system set log_archive_dest_state_<n> = enable` only after DG-07 is clear.

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
