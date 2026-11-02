-- Standby only: transport and apply lag in seconds; -1 = not applicable (primary) or unknown (no redo yet).
-- V$DATAGUARD_STATS.VALUE is '+DD HH:MI:SS'.
select nvl(max(case when name = 'transport lag' then s end), -1) transport_lag_s,
       nvl(max(case when name = 'apply lag' then s end), -1) apply_lag_s,
       nvl(max(case when name = 'apply finish time' then s end), -1) apply_finish_s
  from (select name,
               extract(day from to_dsinterval(value)) * 86400 + extract(hour from to_dsinterval(value)) * 3600
             + extract(minute from to_dsinterval(value)) * 60 + extract(second from to_dsinterval(value)) s
          from v$dataguard_stats where name in ('transport lag', 'apply lag', 'apply finish time') and value is not null)
