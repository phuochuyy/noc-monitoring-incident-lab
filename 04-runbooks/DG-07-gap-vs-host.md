# DG-07-gap-vs-host: Redo gap larger than the host can hold

**Severity:** High

## Why it matters
Cross-host trigger: gap (database host) vs free space of the KVM host minus 2 GB. This is the exact condition of the 02:58 incident.

## Check
1. Gap item of the primary, `df -h /` on the host.

## Fix
1. Keep transport deferred. Free host space (HOST-01) or re-create the standby (`RESTORE ... FROM SERVICE`).

## Escalate
Never enable transport while this is open.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
