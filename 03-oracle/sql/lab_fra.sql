-- FRA (one row). V$RECOVERY_FILE_DEST counts only files the FRA manages: on 2026-10-29 orcl showed 16 %
-- while +FRA had 208 MB of 20 GB free and the primary hung (Stuck Archiver) -> also the disk group and the
-- archived logs written there outside the FRA (never auto-deleted).
select round(f.space_used / f.space_limit * 100, 1) used_pct,
       round(f.space_reclaimable / f.space_limit * 100, 1) reclaimable_pct,
       nvl((select round((total_mb - free_mb) / total_mb * 100, 1) from v$asm_diskgroup g
         where '+' || g.name = upper(p.value) and total_mb > 0), -1) dg_used_pct,   -- -1: FRA not in ASM
       (select count(*) from v$archived_log where deleted = 'NO' and is_recovery_dest_file = 'NO'
           and name like p.value || '%') unmanaged_logs
  from v$recovery_file_dest f, v$parameter p where p.name = 'db_recovery_file_dest'
