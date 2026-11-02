# BK-04-rman-failed: RMAN job failed in the last 24 h

**Severity:** Warning

## Why it matters
A failed job may leave no newer backup; it is also logged where the job ran.

## Check
1. `select start_time, operation, status from v$rman_status where status like 'FAILED%' and start_time > sysdate - 1`
1. RMAN log of the job.

## Fix
1. Fix and re-run the job; confirm with BK-01..03.

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
