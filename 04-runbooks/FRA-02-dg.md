# FRA-02-dg: FRA disk group > 90 % used

**Severity:** High

## Why it matters
V$RECOVERY_FILE_DEST counts only files the FRA manages. 2026-10-29 orcl showed 16 % while +FRA had 208 MB of 20 GB free and the primary hung (Stuck Archiver).

## Check
1. `asmcmd lsdg`
1. FRA-03 (files outside the FRA).

## Fix
1. Move or delete files outside the FRA; check `log_archive_dest_1` = `USE_DB_RECOVERY_FILE_DEST`.

## Escalate
Immediately if the archiver is stuck.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
