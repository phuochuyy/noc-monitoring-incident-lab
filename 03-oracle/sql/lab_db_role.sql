-- Role and protection state of the database (one row). Read-only user C##MON (SELECT_CATALOG_ROLE).
-- FS_FAILOVER_STATUS / OBSERVER_PRESENT: FSFO must stay SYNCHRONIZED with an observer (P1 failover tests).
select db_unique_name, database_role, open_mode, protection_mode, protection_level,
       fs_failover_status, fs_failover_observer_present observer_present, flashback_on, force_logging,
       (select count(*) from gv$instance where status = 'OPEN') instances_open
  from v$database
