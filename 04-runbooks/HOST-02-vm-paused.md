# HOST-02-vm-paused: One or more VMs paused

**Severity:** High

## Why it matters
QEMU pauses a guest when a disk write gets ENOSPC (default `werror=enospc`) - on this host that means the file system holding the images is full.

## Check
1. `virsh -c qemu:///system list --state-paused`
1. `virsh -c qemu:///system domstate <vm> --reason` (ioerror?)
1. `df -h /`

## Fix
1. Free space first (HOST-01), then `virsh -c qemu:///system resume <vm>`.
1. Check each resumed database: alert log, `show configuration` (DGMGRL), GoldenGate processes.

## Escalate
Immediately: paused primaries stop the service.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
