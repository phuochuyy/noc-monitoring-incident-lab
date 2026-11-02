# NOC Monitoring & Incident Response Lab

Monitoring my own Oracle lab (RAC + Data Guard + GoldenGate Active-Active on 8 KVM VMs, Oracle AI Database
26ai = 23.26) the way an operations team runs it: **detect → ticket → handle or escalate → log → report**.
Every alert is tied to an incident I actually had in the lab and has a runbook.

Related projects: [HA/DR failover](https://github.com/phuochuyy/oracle-ha-dr-failover-lab) ·
[backup & recovery drills](https://github.com/phuochuyy/oracle-backup-recovery-drills) ·
[security & compliance](https://github.com/phuochuyy/oracle-security-compliance-lab) ·
[DBA automation & CDC](https://github.com/phuochuyy/oracle-dba-automation-cdc).

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Zabbix 7.0 LTS, agent 2, Oracle checks as SQL, role-aware triggers, runbooks, maintenance per lab scenario, time-to-detect | **done** (this page) |
| 2 | Alert → ticket (Jira Service Management), priority matrix (impact × urgency), escalation | planned |
| 3 | Shift checklist every 8 h, handover and monthly report (availability, MTTD/MTTR, noisy alerts), Grafana | planned |
| 4 | Fault-injection drills with postmortems (MTTD / MTTR) | planned |

## What it watches

```
KVM host (Debian, 23 GB RAM)
  rootless Podman:  PostgreSQL 16 <- Zabbix server 7.0.32 :10051 <- web UI (127.0.0.1:8080)
  agent 2 (lab user, active checks -> 127.0.0.1:10051)
    - host: free bytes of /, VM state (libvirt), thin provisioning
    - Oracle plugin: 9 SQL files, read-only user C##MON over SQL*Net (TNS, both RAC nodes)
          |
          v
VMs (Oracle Linux 9, Oracle 23.26): orcl RAC, orcl_stb RAC, orcl3, orcl3_stb   (no agent in the VMs yet)
```

| Area | Checks | Incident behind it |
|------|--------|--------------------|
| Host storage | free bytes < 12 GB / < 5 GB, 24 h forecast, paused VMs, thin-provisioning cover | host 100 % full, 4 VMs paused (gap of 3.7 GB pulled by a standby) |
| Data Guard | role, FSFO + observer, apply / transport lag, destination errors, **redo gap in MB**, gap vs host space (cross-host), gap logs already deleted | standby stopped applying while FSFO said synchronized; the 3.7 GB gap above |
| Backup | oldest datafile since level 0 / since level 0 or 1, archived-log backup age, failed RMAN jobs | `flock -n` silently skipped a level 1 |
| FRA | % used, FRA **disk group** used, archived logs outside the FRA | view said 16 % while `+FRA` was full → Stuck Archiver |
| Security | accounts `LOCKED(TIMED)`, failed logons (audit), TDE keystore not open | stale wallet locked `DBFS_USER` → DBFS and GoldenGate down; `DBSNMP` locked by the Grid agent |
| GoldenGate | capture not ENABLED, required checkpoint age | a 0-item "phantom" transaction pinned the capture checkpoint for 3 days |

Templates, hosts and triggers are code: [`01-stack/configure.py`](01-stack/configure.py) (idempotent,
`configuration.import`). SQL: [`03-oracle/sql/`](03-oracle/sql). Runbooks: [`04-runbooks/`](04-runbooks).

## Design decisions

| Decision | Why |
|----------|-----|
| **No runbook, no trigger** (23 runbooks: why it matters, check, fix, escalate, close) | an alert nobody knows how to act on is noise (ITIL 4 Monitoring & Event Management) |
| **Role-aware triggers** (`V$DATABASE.DATABASE_ROLE`) | after a Data Guard failover the same template is right without changes; standby-only and primary-only checks never fire on the wrong side |
| **Dependencies**: every database trigger depends on *Oracle unreachable* | a down database is one problem, not twenty |
| **Planned downtime is a maintenance window** ([`maintenance.py`](01-stack/maintenance.py) `<scenario>`) | the lab runs one of 5 scenarios; databases stopped on purpose are suppressed, not ignored. `{$FSFO.EXPECTED}` follows the scenario |
| **Thresholds in bytes, % only as a backstop** | the standard template alerts on % used: on this 278 GB disk 89.8 % used was still 28.9 GB free (first false positive) |
| **Read-only monitoring user** `C##MON` (no new user, no `SELECT ANY DICTIONARY`), password as a Zabbix **secret macro** copied from the Ansible Vault of P3 | least privilege; nothing secret in the repo or on a command line |
| **Active checks only**, web UI on 127.0.0.1 | no port opened to the network; rootless Podman would see the agent through the DHCP address anyway |
| Short **history 7 days, trends 90 days** | disk is the scarce resource of this lab (the stack uses 495.6 MB of images + 230 MB of volumes today) |

## Results (scenario `gg`: prm1 + prm3)

| Measure | Result | Evidence |
|---------|--------|----------|
| Time to detect, host disk below threshold (3 runs) | **34.0 / 34.4 / 35.6 s**; resolved **53.7 / 55.0 / 55.4 s** after the fix | [`results/phase1-mttd-r1.log`](results/phase1-mttd-r1.log) |
| Same condition before this project | not detected: host space was checked by hand (`df`); the hourly health check runs inside the VMs, which cannot see the host's free space | [check_backup_health.sh](https://github.com/phuochuyy/oracle-backup-recovery-drills/blob/main/04-scripts/check_backup_health.sh) header |
| **Real finding** on the first run | orcl3 datafile #34 (`audit_tb`, PDB PERF, created 2026-11-02 03:45) **never backed up**: unprotected until the next level 1 | [`results/raw/orcl3-unbacked-datafiles-r1.txt`](results/raw/orcl3-unbacked-datafiles-r1.txt), [snapshot](results/phase1-snapshot-r1.json) |
| Redo a deferred standby would pull if transport were enabled | orcl3 → stb3 **2,134 MB**, orcl → orcl_stb **246 MB** | [snapshot](results/phase1-snapshot-r1.json) |
| Thin provisioning of the host | images may still grow by 172,082,642,944 B; free 26,812,960,768 B → free space covers **15.6 %** of the possible growth | [snapshot](results/phase1-snapshot-r1.json) |
| Cost of the stack | **132 MB** RAM (61.75 + 36.93 + 33.75 MB), images 495.6 MB, volumes 230 MB | [`results/phase1-stack-memory-r1.txt`](results/phase1-stack-memory-r1.txt) |
| Size | 438 items; 2 lab templates; 20 template triggers + 4 cross-host (DG-07) + 4 host storage triggers | [snapshot](results/phase1-snapshot-r1.json), `configure.py` |

The drill ([`05-drills/mttd.py`](05-drills/mttd.py)) raises the threshold macro above the free space: it
measures the pipeline (config sync → next 1-minute value → trigger → problem), not a real disk filling up.
Detection always landed at second :28 of the minute, the item's schedule: time to detect is bounded by the
item interval.

## Mistakes and false positives (full list: [`notes/worklog.md`](notes/worklog.md))

- **False positive 1:** `FS [/]: Space is low (used > 85%)` with 28.9 GB free → byte thresholds + forecast.
- **False positive 2:** the 24 h forecast fired minutes after the VMs booted (30 min of samples) → forecast
  only with ≥ 5 h of data.
- My errors: `{ITEM.LASTVALUEn}` counted wrongly in trigger names; a filter that missed the RAC keystore
  (`WRL_TYPE = ASM`, not `FILE`); NULLs from SQL rejected by numeric items; 3 s default timeout of active
  checks in 7.0.

## Limits

- Validated on the two primaries of scenario `gg` only. Standby-side checks (apply / transport lag, standby
  role) and FSFO checks are written but **not yet validated** against a running standby (`dg-a`).
- Drills D2 (stop a GoldenGate Extract) and D3 (stop a listener) are designed but were not run.
- One Zabbix server, no HA; the containers do not start with the host (`podman-compose up -d`).
- The host agent runs as the lab user (needs libvirt and the Instant Client). No agent inside the VMs yet:
  OS-level checks of the guests (CPU, memory, file systems, alert logs) are the next step.
- Lab environment: thresholds (backup hours, lag) follow the lab's schedules, not a bank's SLA.

## Run it

```bash
cd 01-stack && cp ../lab.env.example ../lab.env && chmod 600 ../lab.env   # set passwords
podman-compose up -d && python3 bootstrap.py && python3 configure.py
~/work/tools/venvs/dba/bin/python set_secrets.py           # C##MON password -> secret macro
../02-agents/host/install-host-agent.sh                     # systemd --user agent
python3 maintenance.py gg                                   # after labctl.sh gg
python3 ../05-drills/mttd.py d1-disk 3 r1                   # time-to-detect drill
```
