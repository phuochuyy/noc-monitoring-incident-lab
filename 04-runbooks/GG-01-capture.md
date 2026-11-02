# GG-01-capture: GoldenGate capture not ENABLED (primary)

**Severity:** High

## Why it matters
Active-Active replication stops in one direction; changes pile up in the redo the capture still needs.

## Check
1. `gg.sh <node> GG_A "info all"` ([https://github.com/phuochuyy/oracle-ha-dr-failover-lab](https://github.com/phuochuyy/oracle-ha-dr-failover-lab) tests/), `select capture_name, status, error_message from dba_capture` in the PDB.
1. After a lab start: EXTA can be ABENDED with ORA-03111 (known).

## Fix
1. `start extract exta` (AdminClient); GG_B only showing adminsrvr: `systemctl restart ogg-ha` on prm3.
1. Then insert one test row each way and delete it (lab-safety rule).

## Escalate
Replication owner if it abends again.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
