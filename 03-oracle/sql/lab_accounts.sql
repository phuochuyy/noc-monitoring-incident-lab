-- Accounts locked by failed logins (LOCKED(TIMED)) and expired accounts, all containers (one row).
-- Why: 2026-11-01 22:16 prm2 started with an old DBFS wallet -> 10 x ORA-01017 -> DBFS_USER LOCKED(TIMED)
-- -> DBFS and GoldenGate GG_A down; 2026-11-01 16:54 DBSNMP locked by the Grid CVU agent (old wallet).
select count(*) locked_timed,
       nvl(listagg(username || '@' || con_id, ',') within group (order by username), '-') locked_list
  from cdb_users
 where account_status like '%LOCKED(TIMED)%' and oracle_maintained = 'N'
    or account_status like '%LOCKED(TIMED)%' and username in ('DBSNMP', 'GGSYS', 'DBSFWUSER')
