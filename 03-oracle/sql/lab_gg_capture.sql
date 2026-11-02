-- GoldenGate integrated capture (one row per capture, all PDBs).
--   lag_s        = how old the last captured change is
--   ckpt_age_h   = age of the archived log holding REQUIRED_CHECKPOINT_SCN: logs from there on must be kept
-- Why: a "phantom" transaction (0 items, after a failover on 2026-10-29) pinned OGG$CAP_EXTA's checkpoint for
-- 3 days -> archived logs could not be deleted; nothing alerted (fixed with SKIPTRANS on 2026-11-01).
select c.capture_name, c.status, c.con_id,
       nvl((select round((sysdate - max(g.capture_message_create_time)) * 86400) from gv$goldengate_capture g
         where g.capture_name = c.capture_name), -1) lag_s,
       (select max(g.state) from gv$goldengate_capture g where g.capture_name = c.capture_name) state,
       -- archived log holding the SCN, else the online log (SCN not archived yet), else -1
       coalesce((select round((sysdate - max(l.first_time)) * 24, 1) from v$archived_log l
                  where l.first_change# <= c.required_checkpoint_scn and l.next_change# > c.required_checkpoint_scn),
                (select round((sysdate - max(o.first_time)) * 24, 1) from v$log o
                  where o.first_change# <= c.required_checkpoint_scn), -1) ckpt_age_h
  from cdb_capture c
