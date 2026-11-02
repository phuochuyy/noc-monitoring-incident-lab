-- Failed logons (ORA-01017 wrong password, ORA-28000 locked) in the last 10 minutes, all containers.
-- Empty user names are excluded: on the standby the Broker/MMON internal connections (kgfn) fail once with
-- an empty user and succeed on retry - known and accepted (P2 finding 1b). Unified audit on a standby also
-- holds the primary's records (shipped in redo): rate failed logons on primaries only.
select count(*) failed_10m,
       count(distinct dbusername) users,
       nvl(max(dbusername) keep (dense_rank last order by event_timestamp), '-') last_user
  from cdb_unified_audit_trail
 where action_name = 'LOGON' and return_code in (1017, 28000) and dbusername is not null
   and event_timestamp > systimestamp - interval '10' minute
