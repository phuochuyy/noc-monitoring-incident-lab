# SEC-01-locked: Account locked by failed logins

**Severity:** High

## Why it matters
A service account with a stale password locks itself and takes its service down. 2026-11-01 22:16 DBFS_USER (old wallet on prm2) -> DBFS + GoldenGate GG_A down; 16:54 DBSNMP (old CVUDB wallet of Grid).

## Check
1. Item *Accounts locked (list)*.
1. Who failed: `select event_timestamp, dbusername, userhost, client_program_name from unified_audit_trail where return_code = 1017 order by 1 desc fetch first 20 rows only` (in the container shown after @).

## Fix
1. Fix the client first (wallet, `crsctl modify wallet -type CVUDB`, XAG password per cluster), then `alter user <u> account unlock`.
1. Unlocking before fixing the client only locks it again.

## Escalate
Security owner if the source is unknown (possible password guessing).

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
