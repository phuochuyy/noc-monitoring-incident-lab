# DG-05-dest-error: Standby destination in ERROR

**Severity:** High

## Why it matters
The primary cannot ship redo; with FSFO and ASYNC it keeps running, unprotected.

## Check
1. `select dest_id, status, error from v$archive_dest where status <> 'INACTIVE'`.

## Fix
1. Fix the cause (standby down, password file, TNS, network); the destination recovers by itself after the next log switch.

## Escalate
Data Guard owner.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
