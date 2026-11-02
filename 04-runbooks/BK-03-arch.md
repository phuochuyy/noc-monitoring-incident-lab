# BK-03-arch: No archived log backup within 1 h

**Severity:** Warning

## Why it matters
Archived log backups every 30 min bound the data loss of a full restore (RPO).

## Check
1. `systemctl status orcl3-backup@arch`; FRA (FRA-01).

## Fix
1. `systemctl start orcl3-backup@arch`.

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
