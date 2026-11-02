-- Primary: each standby destination, its status, and the redo it has not received yet (MB, logs, logs already
-- deleted here = FAL cannot ship them). Same logic as oracle-backup-recovery-drills check_backup_health.sh 7c.
-- Why: 2026-11-02 02:58 transport to stb3 was switched on with a ~3.7 GB gap on a thin-provisioned host with
-- ~3.5 GB free -> host 100 %, 4 VMs paused.
with inc as (select resetlogs_change# r from v$database_incarnation where status = 'CURRENT'),
     dst as (select dest_id, status, nvl(error, '-') error, db_unique_name
               from v$archive_dest where target = 'STANDBY' and destination is not null and status <> 'INACTIVE'),
     rcv as (select l.dest_id, l.thread#, max(l.sequence#) s from v$archived_log l, inc
              where l.standby_dest = 'YES' and l.resetlogs_change# = inc.r group by l.dest_id, l.thread#),
     loc as (select l.thread#, l.sequence#, l.blocks * l.block_size b, l.deleted from v$archived_log l, inc
              where l.standby_dest = 'NO' and l.resetlogs_change# = inc.r
                and l.dest_id = (select min(dest_id) from v$archive_dest where target = 'PRIMARY' and status = 'VALID'))
select d.dest_id, d.db_unique_name, d.status, d.error,
       round(nvl(sum(case when loc.sequence# > nvl(rcv.s, 0) then loc.b end), 0) / 1048576) gap_mb,
       count(case when loc.sequence# > nvl(rcv.s, 0) then 1 end) gap_logs,
       count(case when loc.sequence# > nvl(rcv.s, 0) and loc.deleted = 'YES' then 1 end) gap_deleted
  from dst d cross join loc left join rcv on rcv.dest_id = d.dest_id and rcv.thread# = loc.thread#
 group by d.dest_id, d.db_unique_name, d.status, d.error
 order by d.dest_id
