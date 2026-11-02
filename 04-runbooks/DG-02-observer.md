# DG-02-observer: FSFO observer not present

**Severity:** Warning

## Why it matters
Without an observer FSFO cannot fail over automatically (Region A: obs-r1, Region B: obs-r2).

## Check
1. `virsh -c qemu:///system domstate obs-r1`
1. `dgmgrl`: `show observer`

## Fix
1. Start the observer VM with `labctl.sh` (it starts the observer service).
1. Note: when RAM is short the observer is sometimes stopped on purpose (CDC tests) - then FSFO is not protected; say so in the shift log.

## Escalate
-

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
