# DG-06-gap: Standby is > 1 GB of redo behind

**Severity:** Warning

## Why it matters
A deferred standby (DEFERRED in the dg-a scenario for orcl3) will pull the whole gap when transport is enabled. 2026-11-02 02:58 a 3.7 GB gap filled the host.

## Check
1. Item *Redo not yet received by a standby (max)* and the host free space.

## Fix
1. Do not enable transport unless host free > gap + 2 GB (DG-07). Otherwise: free space first, or rebuild the standby from a fresh backup instead.

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
