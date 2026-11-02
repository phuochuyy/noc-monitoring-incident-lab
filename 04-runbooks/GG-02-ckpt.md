# GG-02-ckpt: GoldenGate checkpoint pinned > 6 h

**Severity:** Warning

## Why it matters
The archived log holding REQUIRED_CHECKPOINT_SCN and every later one must be kept. 2026-11-01: a 0-item phantom transaction (left by a failover on 10-29) pinned OGG$CAP_EXTA for 3 days.

## Check
1. `gg.sh prm1 GG_A "send extract exta, showtrans"`
1. `select xid from gv$transaction` for the XID shown.

## Fix
1. Only if Items = 0 and the XID is not in GV$TRANSACTION: `send extract exta, skiptrans <xid>` (no THREAD); the checkpoint moves on.

## Escalate
Replication owner if Items > 0 (a real long transaction: ask its owner).

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
