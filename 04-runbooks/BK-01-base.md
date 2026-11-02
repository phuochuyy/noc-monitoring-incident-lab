# BK-01-base: No level 0 base within 170 h

**Severity:** Average

## Why it matters
Level 1 backups need a level 0 base; restore time and risk grow with the age of the base. The week of 2026-11-01 the level 0 was deferred on purpose (host disk) - an expected alert until the next one.

## Check
1. `04-scripts/check_backup_health.sh` on the database VM (same rule).
1. `systemctl list-timers 'orcl3-backup*'` (orcl3), backup logs in `/u02/backup/logs`.

## Fix
1. 9999 h = a datafile that was never backed up (a tablespace created after the last backup): a level 1 also backs up new files as a full copy - run `systemctl start orcl3-backup@1` instead of waiting for the night.
1. Run the level 0 when the host has space (≈ 2.3 GB for orcl3; ≈ 2.8 GB for the RAC offload on stb1).
1. RAC: offload on the standby; after a failover `RESYNC CATALOG` from the primary first (ORA-20079) - see [https://github.com/phuochuyy/oracle-backup-recovery-drills](https://github.com/phuochuyy/oracle-backup-recovery-drills).

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
