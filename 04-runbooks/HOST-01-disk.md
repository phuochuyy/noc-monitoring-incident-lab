# HOST-01-disk: KVM host `/` free < 12 GB (average), < 5 GB (high), or forecast below 12 GB within 24 h

**Severity:** Average/High

## Why it matters
VM disks are thin-provisioned (sparse qcow2/raw, `discard=unmap`). Guests can write far more than the host has: the images may grow by ~174 GB while ~28 GB are free (item *Thin: free space covers % of possible growth*). 2026-11-02 02:58 the host hit 100 % and 4 VMs paused.

## Check
1. `df -h /` and `du -sh /opt/lab/oracle-rac/*` on the host.
1. Which VM grows: `virsh -c qemu:///system domblkinfo <vm> <disk>` (Allocation vs Capacity).
1. Is a standby pulling a redo gap? See DG-06 / DG-07.

## Fix
1. Inside the running VMs: `fstrim -av` (returns freed blocks to the host).
1. `~/work/lab/labctl.sh trim <vm...>` (safe since 2026-11-02: it no longer deletes archived logs).
1. Archived logs already applied on a standby: delete with RMAN (`delete archivelog all completed before 'sysdate-1'` on the standby, after checking `required_checkpoint_scn` of GoldenGate - GG-02).

## Escalate
High (< 5 GB): stop heavy work (load, drills, enabling transport) until > 12 GB.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
