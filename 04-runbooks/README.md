# Runbooks

One per trigger (the trigger URL opens it). Format: why it matters, check, fix, escalate.

| ID | Trigger | Severity |
|----|---------|----------|
| [HOST-01-disk](HOST-01-disk.md) | KVM host `/` free < 12 GB (average), < 5 GB (high), or forecast below 12 GB within 24 h | Warning/Average/High |
| [HOST-02-vm-paused](HOST-02-vm-paused.md) | One or more VMs paused | High |
| [DB-01-unreachable](DB-01-unreachable.md) | Oracle unreachable (3 failed C##MON logins in a row) | High |
| [DG-01-fsfo](DG-01-fsfo.md) | FSFO not synchronized on the primary | Average |
| [DG-02-observer](DG-02-observer.md) | FSFO observer not present | Warning |
| [DG-03-apply-lag](DG-03-apply-lag.md) | Standby apply lag > 5 min | Average |
| [DG-04-transport-lag](DG-04-transport-lag.md) | Standby transport lag > 60 s | Warning |
| [DG-05-dest-error](DG-05-dest-error.md) | Standby destination in ERROR | High |
| [DG-06-gap](DG-06-gap.md) | Standby is > 1 GB of redo behind | Warning |
| [DG-07-gap-vs-host](DG-07-gap-vs-host.md) | Redo gap larger than the host can hold | High |
| [DG-08-gap-deleted](DG-08-gap-deleted.md) | Gap logs already deleted on the primary | Average |
| [BK-01-base](BK-01-base.md) | No level 0 base within 170 h | Average |
| [BK-02-incr](BK-02-incr.md) | No level 0/1 within 26 h | Average |
| [BK-03-arch](BK-03-arch.md) | No archived log backup within 1 h | Warning |
| [BK-04-rman-failed](BK-04-rman-failed.md) | RMAN job failed in the last 24 h | Warning |
| [FRA-01-used](FRA-01-used.md) | FRA used > 80 % | Warning |
| [FRA-02-dg](FRA-02-dg.md) | FRA disk group > 90 % used | High |
| [FRA-03-unmanaged](FRA-03-unmanaged.md) | Archived logs in the FRA disk group outside the FRA | Warning |
| [SEC-01-locked](SEC-01-locked.md) | Account locked by failed logins | High |
| [SEC-02-failed-logons](SEC-02-failed-logons.md) | ≥ 5 failed logons in 10 min (primary) | Warning |
| [SEC-03-tde](SEC-03-tde.md) | TDE keystore not open | High |
| [GG-01-capture](GG-01-capture.md) | GoldenGate capture not ENABLED (primary) | High |
| [GG-02-ckpt](GG-02-ckpt.md) | GoldenGate checkpoint pinned > 6 h | Warning |
