# Worklog

Problems met, causes, fixes and lessons (including my own mistakes).

## Phase 1 - build (no VM running yet)

| Problem | Cause | Fix / lesson |
|---------|-------|--------------|
| Default `Admin/zabbix` login on a fresh server | image default | `bootstrap.py` replaces it on first run; password only in `lab.env` (600, git-ignored) |
| Server (rootless Podman) reaches the host agent from the LAN address (`192.168.0.197`, DHCP), not from loopback | Podman `pasta` networking | active checks only: agents connect out to `:10051`, nothing listens on the network (agent passive port on 127.0.0.1) |
| Packaged agent runs as `zabbix`: no libvirt, no Instant Client | packaging | agent 2 as the lab user (`systemd --user`), config in the repo |
| `Plugins.Oracle.CustomQueriesEnabled: unknown parameter` | option copied from a newer version; agent 2 here is 7.0.22 | removed; `CustomQueriesPath` alone enables custom queries in 7.0 |
| `configuration.import`: `UUIDv4 is expected` | my uuid5 values (deterministic) carry version 5 | same bytes with the version bits set to 4: still deterministic, re-runs update instead of duplicating |
| LLD rule needs an agent interface | type defaulted to passive | discovery rule and prototypes `ZABBIX_ACTIVE` |
| Trigger names showed the wrong values (my mistake) | `{ITEM.LASTVALUEn}` counts items in expression order; I counted macros, and pointed at items not in the expression | indexes fixed, values outside the expression removed |
| `__pycache__` in the first commit (my mistake) | no `.gitignore` entry | ignored, commit amended before push |
| First problem was a false positive: `FS [/]: Space is low (used > 85%)` with 28.9 GB free (item `vfs.fs.dependent[/,data]` at 21:2x: used 253,714,558,976 B, free 28,893,040,640 B, pused 89.776 %) | the 7.0 standard template alerts on % used only; on a 278 GB disk (ext4 5 % reserve) 89.8 % used = 28.9 GB free, above the lab rule (12 GB) | free-bytes triggers (< 12 GB average, < 5 GB high) + a 24 h forecast (`timeleft`, 6 h trend) in Lab KVM host; the % triggers raised to 99 / 99.5 as a backstop so one condition pages once. Resolved by itself after the change |

## Phase 1 - first run against the databases (scenario gg: prm1 + prm3)

| Problem | Cause | Fix / lesson |
|---------|-------|--------------|
| Oracle items: `Timeout occurred while gathering data` | in 7.0 the item timeout of active checks comes from the server (default 3 s); connect + query took longer during database start-up | item timeout 20 s on the query items, 10 s on the ping; the backup query takes 0.13 s on orcl once open |
| Lag, FRA disk group, GoldenGate age: `Value "null" is not suitable for Numeric` | JSONPath found the key, value SQL NULL (primary has no lag; orcl3 FRA is a file system) | `nvl(..., -1)` in the SQL: -1 = not applicable; no trigger fires on -1 |
| orcl TDE showed 0 containers | my filter `wrl_type = 'FILE'`; the RAC keystore is in ASM (`WRL_TYPE = ASM`) | filter removed: 6 containers OPEN / AUTOLOGIN on both databases |
| GoldenGate checkpoint age -1 | REQUIRED_CHECKPOINT_SCN in the current online log, not archived yet | fall back to V$LOG: 0.1-0.2 h |
| `10 Kh`, `2.1 KMB` in problem names | Zabbix unit prefixes applied to h and MB | units `!h`, `!MB` (no conversion); old events keep the old name |
| Second false positive: `/ will drop below 12G within 24 h` | VMs booting: free space dropped fast for minutes; `timeleft` over 30 min of samples | forecast only with >= 300 samples (5 h) in the 6 h window; resolved |
| **Real finding:** orcl3 `no level 0 base for 9999` | datafile #34 (`audit_tb`, created 2026-11-02 for case 10) was never backed up; next level 1 (02:00) would take it | correct alert: a new tablespace is unprotected until the next backup - see runbook BK-01 |

## Phase 1 - change for the network lab (2026-11-02 23:2x)

| Problem | Cause | Fix / lesson |
|---------|-------|--------------|
| ICMP items: `fping: Operation not permitted` | rootless container without raw sockets | `cap_add: [NET_RAW]` on the server container; fping 0 % loss to 3 hosts |
| **My mistake:** the Zabbix server was down for about 70 s (stopped ~23:28, back 23:29:08) | podman-compose 1.3 does not recreate a running container; I stopped and removed `zbx-server` by hand without seeing that `zbx-web` depends on it, so the removal failed with the server already stopped | recreated web + server; lesson: a change to the monitoring stack is a change like any other - plan the order (`down` / `up` of the whole stack) and say when monitoring is blind |
