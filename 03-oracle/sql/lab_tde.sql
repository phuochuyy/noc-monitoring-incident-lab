-- TDE keystore per container: anything but OPEN means encrypted tablespaces cannot be read (and on a standby,
-- redo apply stops at the next encrypted change). After every SET KEY the keystore must be copied to the
-- standby (lab-safety rule).
select count(*) containers,
       count(case when status <> 'OPEN' and status <> 'OPEN_NO_MASTER_KEY' then 1 end) not_open,
       nvl(listagg(case when status <> 'OPEN' then con_id || ':' || status end, ',') within group (order by con_id), '-') detail,
       max(wallet_type) wallet_type
  from v$encryption_wallet   -- WRL_TYPE FILE (orcl3) or ASM (orcl RAC): both count
