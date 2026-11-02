# FRA-03-unmanaged: Archived logs in the FRA disk group outside the FRA

**Severity:** Warning

## Why it matters
Logs written with `LOCATION=+FRA` instead of `USE_DB_RECOVERY_FILE_DEST` are never deleted automatically (the cause of FRA-02 on 2026-10-29).

## Check
1. `select name from v$archived_log where is_recovery_dest_file = 'NO' and deleted = 'NO'`

## Fix
1. Fix the destination parameter; back up and delete those logs with RMAN.

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
