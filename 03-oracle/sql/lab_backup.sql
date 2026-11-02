-- Backup age in hours (one row). Same rules as check_backup_health.sh 1:
--   base_h  = oldest datafile since its last level 0 (or a level 1 that is a full copy of a new file);
--             a file whose checkpoint did not move since its last backup counts as current (PDB$SEED)
--   incr_h  = oldest datafile since its last level 0 or 1
--   arch_h  = last archived log backup; failed_24h = RMAN jobs FAILED in the last 24 h
-- Only meaningful where backups run ({$BACKUP.HERE} on the host): orcl backs up on its standby.
select (select max(h) from (select case when d.checkpoint_change# <= max(b.checkpoint_change#) then 0
                                        else nvl((sysdate - max(b.completion_time)) * 24, 9999) end h
                              from v$datafile d left join v$backup_datafile b on b.file# = d.file#
                                   and (b.incremental_level = 0 or b.incremental_change# <= b.creation_change#)
                             group by d.file#, d.checkpoint_change#)) base_h,
       (select max(h) from (select case when d.checkpoint_change# <= max(b.checkpoint_change#) then 0
                                        else nvl((sysdate - max(b.completion_time)) * 24, 9999) end h
                              from v$datafile d left join v$backup_datafile b on b.file# = d.file#
                                   and b.incremental_level in (0, 1)
                             group by d.file#, d.checkpoint_change#)) incr_h,
       (select round(nvl((sysdate - max(completion_time)) * 24, 9999), 2) from v$backup_set_details
         where backup_type = 'L') arch_h,
       (select count(*) from v$rman_status where start_time > sysdate - 1 and status like 'FAILED%'
           and row_level = 0) failed_24h
  from dual
