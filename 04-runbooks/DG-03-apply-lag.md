# DG-03-apply-lag: Standby apply lag > 5 min

**Severity:** Average

## Why it matters
The standby receives redo but does not apply it: a failover would need to apply everything first (longer RTO). The P3 health check once found a standby that had stopped applying while FSFO still showed synchronized.

## Check
1. On the standby: `select process, status, sequence# from v$managed_standby` (MRP0 present?).
1. `dgmgrl`: `show database <stb>` (apply state, errors).
1. Alert log of the standby (ORA-xxxxx at apply, e.g. TDE keystore - SEC-03).

## Fix
1. `dgmgrl`: `edit database <stb> set state='APPLY-ON'`.
1. If apply stops on an encrypted change: copy the keystore from the primary (lab-safety TDE rule), then APPLY-ON.

## Escalate
Data Guard owner if apply does not restart.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
