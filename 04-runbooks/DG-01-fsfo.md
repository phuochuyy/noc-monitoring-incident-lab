# DG-01-fsfo: FSFO not synchronized on the primary

**Severity:** Average

## Why it matters
With FSFO enabled and not SYNCHRONIZED, a failover could lose data or not happen at all. It happened in this lab when the standby FRA filled (ORA-19809).

## Check
1. `dgmgrl` (C##DGADMIN wallet on the observer): `show configuration verbose`, `show fast_start failover`.
1. Standby FRA and archive destination: FRA-01, DG-05.

## Fix
1. Fix the cause (standby down, FRA full, transport error), then `show configuration` until SUCCESS.

## Escalate
Data Guard owner if not SUCCESS within 15 min.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
