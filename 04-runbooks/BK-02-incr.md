# BK-02-incr: No level 0/1 within 26 h

**Severity:** Average

## Why it matters
The daily level 1 did not run. 2026-11-01: `flock -n` silently skipped the level 1 when it met the archived-log job - fixed with `flock -w 1800`.

## Check
1. `systemctl status orcl3-backup@1`, `journalctl -u orcl3-backup@1 -n 50`
1. BK-04 (failed RMAN jobs).

## Fix
1. Run it by hand: `systemctl start orcl3-backup@1` (it waits for the lock, up to 30 min).

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
