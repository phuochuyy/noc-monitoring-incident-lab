# FRA-01-used: FRA used > 80 %

**Severity:** Warning

## Why it matters
When the FRA fills, the archiver stops and so does the database (ORA-19809 / Stuck Archiver).

## Check
1. `select * from v$recovery_area_usage`
1. Reclaimable part (item *FRA reclaimable*).

## Fix
1. Back up archived logs (BK-03) so they become reclaimable; delete applied logs on a standby (deletion policy APPLIED ON ALL STANDBY).
1. Never delete logs GoldenGate still needs (GG-02).

## Escalate
Average if > 90 %.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
