# DB-01-unreachable: Oracle unreachable (3 failed C##MON logins in a row)

**Severity:** High

## Why it matters
Every other database check depends on this one, so a down database shows one problem, not twenty.

## Check
1. Is the VM running (item *VM <name>: running*)? If the scenario stopped it, it should be in maintenance (`01-stack/maintenance.py <scenario>`).
1. Listener: `lsnrctl status` (single instance) or `srvctl status listener` / `srvctl status database -d <db>` (RAC).
1. Account: `select account_status from dba_users where username = 'C##MON'` - a locked monitoring user looks like a down database.

## Fix
1. Start what is down with `srvctl start database -d <db>` (RAC) or `sqlplus / as sysdba` + `startup` (orcl3).
1. If only C##MON is locked: find who used a wrong password (SEC-02) before unlocking.

## Escalate
If the primary of a Data Guard pair is down and FSFO did not fail over: Data Guard owner.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
