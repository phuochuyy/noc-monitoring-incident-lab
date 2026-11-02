"""Zabbix configuration as code: templates, hosts, housekeeping. Idempotent (configuration.import with
createMissing/updateExisting/deleteMissing for the lab templates; host.create/update for hosts).

Design rules (enterprise monitoring practice):
- every trigger has an action: a runbook in ../04-runbooks/<ID>.md (trigger URL) - no runbook, no trigger;
- triggers are role-aware (V$DATABASE.DATABASE_ROLE), so a Data Guard failover needs no reconfiguration;
- thresholds are macros with the reason next to them; per-host overrides live in HOSTS below;
- expected outages (VMs stopped by a lab scenario) are maintenance windows (maintenance.py), not ignored alerts.

usage: python3 configure.py            (reads ../lab.env; the Oracle password macro is set by set_secrets.py)
"""
import json
import uuid

from zbx import Zabbix

NS = uuid.UUID("6f1c2a3e-6d0b-4c55-9a51-0c5e6b7d8a90")
RUNBOOK = "{$RUNBOOK.BASE}/"


def uid(*parts):
    # deterministic (same object -> same uuid on every run), formatted as the UUIDv4 Zabbix requires
    return uuid.UUID(bytes=uuid.uuid5(NS, "/".join(parts)).bytes, version=4).hex


GROUP_T = "Templates/Lab"
T_HOST = "Lab KVM host"
T_DB = "Lab Oracle DBA by agent 2"


# --------------------------------------------------------------------------------------------- KVM host
def kvm_template():
    t = T_HOST
    items = [
        {"name": "VMs paused", "key": "lab.vm.paused.count", "delay": "1m", "value_type": "UNSIGNED",
         "description": "A thin-provisioned host that runs out of space pauses its VMs (I/O error).",
         "triggers": [{"name": "{HOST.NAME}: {ITEM.LASTVALUE} VM(s) paused - host storage full?",
                       "expression": f"last(/{t}/lab.vm.paused.count)>0", "priority": "HIGH",
                       "url": RUNBOOK + "HOST-02-vm-paused.md", "uuid": uid(t, "trg", "paused")}]},
        {"name": "VMs running", "key": "lab.vm.running.count", "delay": "1m", "value_type": "UNSIGNED"},
        {"name": "Host / free", "key": "vfs.fs.size[/,free]", "delay": "1m", "value_type": "UNSIGNED", "units": "B",
         "description": "Free bytes for unprivileged users (ext4 reserve excluded). Also used by DG-07.",
         "triggers": [
             {"name": "{HOST.NAME}: / free {ITEM.LASTVALUE} < {$HOST.FREE.CRIT}", "priority": "HIGH",
              "expression": f"last(/{t}/vfs.fs.size[/,free])<{{$HOST.FREE.CRIT}}",
              "url": RUNBOOK + "HOST-01-disk.md", "url_name": "Runbook HOST-01", "uuid": uid(t, "trg", "free-crit")},
             {"name": "{HOST.NAME}: / free {ITEM.LASTVALUE} < {$HOST.FREE.WARN}", "priority": "AVERAGE",
              "expression": f"last(/{t}/vfs.fs.size[/,free])<{{$HOST.FREE.WARN}}",
              "url": RUNBOOK + "HOST-01-disk.md", "url_name": "Runbook HOST-01", "uuid": uid(t, "trg", "free-warn"),
              "dependencies": [{"name": "{HOST.NAME}: / free {ITEM.LASTVALUE} < {$HOST.FREE.CRIT}",
                                "expression": f"last(/{t}/vfs.fs.size[/,free])<{{$HOST.FREE.CRIT}}"}]},
             {"name": "{HOST.NAME}: / will drop below {$HOST.FREE.WARN} within 24 h (6 h trend)", "priority": "WARNING",
              # needs >= 5 h of samples: right after VMs boot the free space drops fast for minutes and a
              # forecast on 30 min of data said "full within 24 h" (second false positive, 2026-11-02 21:5x)
              "expression": f"timeleft(/{t}/vfs.fs.size[/,free],6h,{{$HOST.FREE.WARN}})<24h and "
                            f"last(/{t}/vfs.fs.size[/,free])>{{$HOST.FREE.WARN}} and "
                            f"count(/{t}/vfs.fs.size[/,free],6h)>=300",
              "url": RUNBOOK + "HOST-01-disk.md", "url_name": "Runbook HOST-01", "uuid": uid(t, "trg", "free-forecast"),
              "description": "Predictive: warns before the threshold while there is still time to act."}]},
        {"name": "Thin provisioning raw", "key": "lab.thin.json", "delay": "10m", "value_type": "TEXT",
         "history": "1d", "description": "VM disk images: apparent vs allocated size, free space (thin.sh)."},
    ]
    for k, name, units in [("growth", "Thin: guests can still grow by", "B"),
                           ("fs_free", "Thin: file system free", "B"),
                           ("cover_pct", "Thin: free space covers % of possible growth", "%")]:
        items.append({"name": name, "key": f"lab.thin.{k}", "type": "DEPENDENT", "value_type": "FLOAT",
                      "units": units, "master_item": {"key": "lab.thin.json"},
                      "preprocessing": [{"type": "JSONPATH", "parameters": [f"$.{k}"]}]})
    lld = {"name": "VM discovery", "key": "lab.vm.discovery", "delay": "10m", "type": "ZABBIX_ACTIVE",
           "uuid": uid(t, "lld", "vm"), "lifetime": "7d",
           "item_prototypes": [{"name": "VM {#VM}: running", "key": "lab.vm.running[{#VM}]", "delay": "1m", "type": "ZABBIX_ACTIVE",
                                "value_type": "UNSIGNED", "uuid": uid(t, "proto", "running"),
                                "valuemap": {"name": "Lab running"}}]}
    for it in items:
        it.setdefault("type", "ZABBIX_ACTIVE")
        it["uuid"] = uid(t, "item", it["key"])
    return {"uuid": uid(t), "template": t, "name": t, "groups": [{"name": GROUP_T}],
            "description": "KVM host of the Oracle lab: VM state, thin provisioning, free bytes of / (the lab rule "
                           "is in GB, not %). CPU, memory, other file systems: 'Linux by Zabbix agent active'.",
            "macros": [{"macro": "{$HOST.FREE.WARN}", "value": "12G", "description": "lab-safety: < 12 GB -> trim first"},
                       {"macro": "{$HOST.FREE.CRIT}", "value": "5G", "description": "stop heavy work"}],
            "items": items, "discovery_rules": [lld],
            "valuemaps": [{"uuid": uid(t, "vm"), "name": "Lab running",
                           "mappings": [{"value": "0", "newvalue": "not running"},
                                        {"value": "1", "newvalue": "running"}]}]}


# --------------------------------------------------------------------------------------------- Oracle
def q(name):
    return ("oracle.custom.query[{$ORACLE.CONN},{$ORACLE.USER},{$ORACLE.PASSWORD},{$ORACLE.SERVICE},"
            f"{name}]")


def dep(t, key, name, master, path, vtype="FLOAT", units="", default="-1", desc=""):
    it = {"uuid": uid(t, "item", key), "name": name, "key": key, "type": "DEPENDENT", "value_type": vtype,
          "units": units, "master_item": {"key": master}, "description": desc,
          "preprocessing": [{"type": "JSONPATH", "parameters": [path],
                             "error_handler": "CUSTOM_VALUE", "error_handler_params": default}]}
    return it


def trg(t, tid, name, expr, prio, opdata="", desc="", deps=None, manual=False):
    d = {"uuid": uid(t, "trg", tid), "name": name, "expression": expr, "priority": prio,
         "url": RUNBOOK + f"{tid}.md", "url_name": f"Runbook {tid}", "opdata": opdata, "description": desc,
         "manual_close": "YES" if manual else "NO"}
    if deps:
        d["dependencies"] = deps
    return d


def db_template():
    t = T_DB
    P = f"last(/{t}/lab.db.role)=\"PRIMARY\""
    S = f"last(/{t}/lab.db.role)=\"PHYSICAL STANDBY\""
    masters = [  # (sql file, key, interval)
        ("lab_db_role", "lab.db.role.json", "1m"), ("lab_dg_lag", "lab.dg.lag.json", "1m"),
        ("lab_standby_dest", "lab.dg.dest.json", "2m"), ("lab_backup", "lab.backup.json", "10m"),
        ("lab_fra", "lab.fra.json", "5m"), ("lab_accounts", "lab.accounts.json", "2m"),
        ("lab_failed_logons", "lab.audit.logons.json", "5m"), ("lab_gg_capture", "lab.gg.capture.json", "2m"),
        ("lab_tde", "lab.tde.json", "5m")]
    items = [{"uuid": uid(t, "item", "ping"), "name": "Oracle: reachable (C##MON login)", "type": "ZABBIX_ACTIVE",
              "key": "oracle.ping[{$ORACLE.CONN},{$ORACLE.USER},{$ORACLE.PASSWORD},{$ORACLE.SERVICE}]",
              "delay": "1m", "value_type": "UNSIGNED", "valuemap": {"name": "Lab up"}, "timeout": "10s"}]
    for sql, key, delay in masters:
        items.append({"uuid": uid(t, "item", key), "name": f"Oracle raw: {sql}", "type": "ZABBIX_ACTIVE",
                      "key": q(sql), "delay": delay, "value_type": "TEXT", "history": "1d", "timeout": "20s",
                      "description": f"03-oracle/sql/{sql}.sql"})
    M = {key: q(sql) for sql, key, _ in masters}
    D = [
        dep(t, "lab.db.role", "DB role", M["lab.db.role.json"], "$[0].DATABASE_ROLE", "CHAR", default="UNKNOWN"),
        dep(t, "lab.db.open_mode", "DB open mode", M["lab.db.role.json"], "$[0].OPEN_MODE", "CHAR", default="UNKNOWN"),
        dep(t, "lab.db.fsfo", "FSFO status", M["lab.db.role.json"], "$[0].FS_FAILOVER_STATUS", "CHAR", default="UNKNOWN"),
        dep(t, "lab.db.observer", "FSFO observer present", M["lab.db.role.json"], "$[0].OBSERVER_PRESENT", "CHAR", default="UNKNOWN"),
        dep(t, "lab.db.protection", "Protection level", M["lab.db.role.json"], "$[0].PROTECTION_LEVEL", "CHAR", default="UNKNOWN"),
        dep(t, "lab.db.instances", "Instances open", M["lab.db.role.json"], "$[0].INSTANCES_OPEN", "UNSIGNED", default="0"),
        dep(t, "lab.dg.transport_lag", "DG transport lag", M["lab.dg.lag.json"], "$[0].TRANSPORT_LAG_S", units="s"),
        dep(t, "lab.dg.apply_lag", "DG apply lag", M["lab.dg.lag.json"], "$[0].APPLY_LAG_S", units="s"),
        dep(t, "lab.dg.dest.errors", "Standby destinations in error", M["lab.dg.dest.json"],
            "$[?(@.STATUS == 'ERROR')].length()", "UNSIGNED", default="0"),
        dep(t, "lab.dg.dest.deferred", "Standby destinations deferred", M["lab.dg.dest.json"],
            "$[?(@.STATUS == 'DEFERRED')].length()", "UNSIGNED", default="0"),
        dep(t, "lab.dg.dest.gap_mb", "Redo not yet received by a standby (max)", M["lab.dg.dest.json"],
            "$[*].GAP_MB.max()", units="!MB", default="0"),
        dep(t, "lab.dg.dest.gap_deleted", "Gap logs already deleted here (need restore)", M["lab.dg.dest.json"],
            "$[*].GAP_DELETED.sum()", "UNSIGNED", default="0"),
        dep(t, "lab.backup.base_h", "Backup: oldest datafile since level 0", M["lab.backup.json"], "$[0].BASE_H", units="!h"),
        dep(t, "lab.backup.incr_h", "Backup: oldest datafile since level 0/1", M["lab.backup.json"], "$[0].INCR_H", units="!h"),
        dep(t, "lab.backup.arch_h", "Backup: last archived log backup", M["lab.backup.json"], "$[0].ARCH_H", units="!h"),
        dep(t, "lab.backup.failed_24h", "RMAN jobs failed (24 h)", M["lab.backup.json"], "$[0].FAILED_24H", "UNSIGNED", default="0"),
        dep(t, "lab.fra.used", "FRA used", M["lab.fra.json"], "$[0].USED_PCT", units="%"),
        dep(t, "lab.fra.reclaimable", "FRA reclaimable", M["lab.fra.json"], "$[0].RECLAIMABLE_PCT", units="%"),
        dep(t, "lab.fra.dg_used", "FRA disk group used", M["lab.fra.json"], "$[0].DG_USED_PCT", units="%"),
        dep(t, "lab.fra.unmanaged", "Archived logs in the FRA disk group not managed by the FRA", M["lab.fra.json"],
            "$[0].UNMANAGED_LOGS", "UNSIGNED", default="0"),
        dep(t, "lab.acct.locked", "Accounts locked by failed logins", M["lab.accounts.json"], "$[0].LOCKED_TIMED", "UNSIGNED", default="0"),
        dep(t, "lab.acct.locked_list", "Accounts locked (list)", M["lab.accounts.json"], "$[0].LOCKED_LIST", "CHAR", default="-"),
        dep(t, "lab.audit.failed_10m", "Failed logons (10 min)", M["lab.audit.logons.json"], "$[0].FAILED_10M", "UNSIGNED", default="0"),
        dep(t, "lab.audit.last_user", "Failed logons: last user", M["lab.audit.logons.json"], "$[0].LAST_USER", "CHAR", default="-"),
        dep(t, "lab.gg.not_enabled", "GoldenGate captures not ENABLED", M["lab.gg.capture.json"],
            "$[?(@.STATUS != 'ENABLED')].length()", "UNSIGNED", default="0"),
        dep(t, "lab.gg.captures", "GoldenGate captures", M["lab.gg.capture.json"], "$.length()", "UNSIGNED", default="0"),
        dep(t, "lab.gg.ckpt_age", "GoldenGate required checkpoint age (max)", M["lab.gg.capture.json"],
            "$[*].CKPT_AGE_H.max()", units="!h"),
        dep(t, "lab.gg.lag", "GoldenGate capture lag (max)", M["lab.gg.capture.json"], "$[*].LAG_S.max()", units="s"),
        dep(t, "lab.tde.not_open", "TDE keystores not open", M["lab.tde.json"], "$[0].NOT_OPEN", "UNSIGNED", default="0"),
        dep(t, "lab.tde.detail", "TDE keystore detail", M["lab.tde.json"], "$[0].DETAIL", "CHAR", default="-"),
    ]
    items += D
    ping = "oracle.ping[{$ORACLE.CONN},{$ORACLE.USER},{$ORACLE.PASSWORD},{$ORACLE.SERVICE}]"
    down = {"name": "{HOST.NAME}: Oracle unreachable", "expression": f"max(/{t}/{ping},3m)=0"}
    triggers = [
        trg(t, "DB-01-unreachable", down["name"], down["expression"], "HIGH",
            desc="3 failed logins of C##MON in a row (listener, instance, network or the account)."),
        trg(t, "DG-01-fsfo", "{HOST.NAME}: FSFO not synchronized ({ITEM.LASTVALUE2})",
            f"{{$FSFO.EXPECTED}}=1 and {P} and last(/{t}/lab.db.fsfo)<>\"SYNCHRONIZED\"", "AVERAGE", deps=[down]),
        trg(t, "DG-02-observer", "{HOST.NAME}: FSFO observer not present",
            f"{{$FSFO.EXPECTED}}=1 and {P} and last(/{t}/lab.db.observer)=\"NO\"", "WARNING", deps=[down]),
        trg(t, "DG-03-apply-lag", "{HOST.NAME}: standby apply lag > {$DG.APPLY.LAG.WARN}s",
            f"{S} and min(/{t}/lab.dg.apply_lag,5m)>{{$DG.APPLY.LAG.WARN}}", "AVERAGE",
            deps=[down],
            desc="Health check of P3 caught a standby that stopped applying while FSFO still said synchronized."),
        trg(t, "DG-04-transport-lag", "{HOST.NAME}: standby transport lag > {$DG.TRANSPORT.LAG.WARN}s",
            f"{S} and min(/{t}/lab.dg.transport_lag,5m)>{{$DG.TRANSPORT.LAG.WARN}}", "WARNING", deps=[down]),
        trg(t, "DG-05-dest-error", "{HOST.NAME}: {ITEM.LASTVALUE2} standby destination(s) in ERROR",
            f"{P} and last(/{t}/lab.dg.dest.errors)>0", "HIGH", deps=[down]),
        trg(t, "DG-06-gap", "{HOST.NAME}: standby is {ITEM.LASTVALUE2} of redo behind",
            f"{P} and last(/{t}/lab.dg.dest.gap_mb)>{{$DG.GAP.WARN.MB}}", "WARNING", deps=[down],
            desc="Gap a deferred standby will pull when transport is enabled. Check host space first (DG-07)."),
        trg(t, "DG-08-gap-deleted", "{HOST.NAME}: {ITEM.LASTVALUE2} gap log(s) already deleted - standby needs a restore",
            f"{P} and last(/{t}/lab.dg.dest.gap_deleted)>0", "AVERAGE", deps=[down]),
        trg(t, "BK-01-base", "{HOST.NAME}: no level 0 base for {ITEM.LASTVALUE} (9999 = a datafile never backed up)",
            f"{{$BACKUP.HERE}}=1 and last(/{t}/lab.backup.base_h)>{{$BACKUP.BASE.MAX.H}}", "AVERAGE", deps=[down]),
        trg(t, "BK-02-incr", "{HOST.NAME}: no level 0/1 for {ITEM.LASTVALUE} (9999 = a datafile never backed up)",
            f"{{$BACKUP.HERE}}=1 and last(/{t}/lab.backup.incr_h)>{{$BACKUP.INCR.MAX.H}}", "AVERAGE", deps=[down]),
        trg(t, "BK-03-arch", "{HOST.NAME}: no archived log backup for {ITEM.LASTVALUE}",
            f"{{$BACKUP.HERE}}=1 and last(/{t}/lab.backup.arch_h)>{{$BACKUP.ARCH.MAX.H}}", "WARNING", deps=[down]),
        trg(t, "BK-04-rman-failed", "{HOST.NAME}: {ITEM.LASTVALUE} RMAN job(s) failed in 24 h",
            f"last(/{t}/lab.backup.failed_24h)>0", "WARNING", deps=[down]),
        trg(t, "FRA-01-used", "{HOST.NAME}: FRA {ITEM.LASTVALUE} used",
            f"last(/{t}/lab.fra.used)>{{$FRA.USED.WARN}}", "WARNING", deps=[down]),
        trg(t, "FRA-02-dg", "{HOST.NAME}: FRA disk group {ITEM.LASTVALUE} used",
            f"last(/{t}/lab.fra.dg_used)>{{$FRA.DG.USED.CRIT}}", "HIGH", deps=[down],
            desc="2026-10-29: FRA view said 16 % while +FRA was full -> Stuck Archiver."),
        trg(t, "FRA-03-unmanaged", "{HOST.NAME}: {ITEM.LASTVALUE} archived log(s) in the FRA disk group outside the FRA",
            f"last(/{t}/lab.fra.unmanaged)>0", "WARNING", deps=[down]),
        trg(t, "SEC-01-locked", "{HOST.NAME}: account(s) locked by failed logins: {ITEM.LASTVALUE2}",
            f"last(/{t}/lab.acct.locked)>0 and length(last(/{t}/lab.acct.locked_list))>0", "HIGH", deps=[down],
            desc="A service account with a stale password (wallet, CRS, XAG) locks itself and takes its service down."),
        trg(t, "SEC-02-failed-logons", "{HOST.NAME}: {ITEM.LASTVALUE2} failed logons in 10 min (last user {ITEM.LASTVALUE3})",
            f"{P} and last(/{t}/lab.audit.failed_10m)>={{$AUDIT.FAILED.WARN}} and length(last(/{t}/lab.audit.last_user))>0",
            "WARNING", deps=[down]),
        trg(t, "SEC-03-tde", "{HOST.NAME}: TDE keystore not open ({ITEM.LASTVALUE2})",
            f"last(/{t}/lab.tde.not_open)>0 and length(last(/{t}/lab.tde.detail))>0", "HIGH", deps=[down]),
        trg(t, "GG-01-capture", "{HOST.NAME}: {ITEM.LASTVALUE2} GoldenGate capture(s) not ENABLED",
            f"{P} and last(/{t}/lab.gg.not_enabled)>0", "HIGH", deps=[down]),
        trg(t, "GG-02-ckpt", "{HOST.NAME}: GoldenGate checkpoint pinned {ITEM.LASTVALUE2} h (archived logs retained)",
            f"{P} and last(/{t}/lab.gg.ckpt_age)>{{$GG.CKPT.MAX.H}}", "WARNING", deps=[down],
            desc="2026-11-01: a 0-item phantom transaction held OGG$CAP_EXTA's checkpoint for 3 days."),
    ]
    macros = [  # value, reason
        ("{$ORACLE.USER}", "c##mon", "read-only monitoring user of P3 (SELECT_CATALOG_ROLE, AUDIT_VIEWER)"),
        ("{$ORACLE.SERVICE}", "-", "unused: {$ORACLE.CONN} is a TNS alias (ResolveTNS)"),
        ("{$FSFO.EXPECTED}", "0", "1 when the lab scenario runs this region with FSFO (maintenance.py sets it)"),
        ("{$DG.APPLY.LAG.WARN}", "300", "seconds; lab standbys apply in real time, 5 min means apply stopped"),
        ("{$DG.TRANSPORT.LAG.WARN}", "60", "seconds; ASYNC transport in the lab"),
        ("{$DG.GAP.WARN.MB}", "1024", "same as GAP_WARN_MB of check_backup_health.sh"),
        ("{$BACKUP.HERE}", "0", "1 where backups run (orcl3 timers, orcl_stb offload)"),
        ("{$BACKUP.BASE.MAX.H}", "170", "weekly level 0 + 2 h"),
        ("{$BACKUP.INCR.MAX.H}", "26", "daily level 1 + 2 h"),
        ("{$BACKUP.ARCH.MAX.H}", "1", "archived log backup every 30 min"),
        ("{$FRA.USED.WARN}", "80", "%"),
        ("{$FRA.DG.USED.CRIT}", "90", "%"),
        ("{$AUDIT.FAILED.WARN}", "5", "failed logons in 10 min"),
        ("{$GG.CKPT.MAX.H}", "6", "provisional - set from the baseline of the first week"),
    ]
    tmpl = {"uuid": uid(t), "template": t, "name": t, "groups": [{"name": GROUP_T}],
            "description": "Oracle checks that map to incidents of the lab (P1-P3), run by the KVM host's agent 2 "
                           "with the read-only user C##MON. SQL in 03-oracle/sql.",
            "items": items,
            "macros": [{"macro": m, "value": v, "description": d} for m, v, d in macros],
            "valuemaps": [{"uuid": uid(t, "up"), "name": "Lab up",
                           "mappings": [{"value": "0", "newvalue": "down"}, {"value": "1", "newvalue": "up"}]}]}
    return tmpl, triggers


# --------------------------------------------------------------------------------------------- hosts
HOSTS = {  # host: (group, templates, macros)
    "kvm-host": ("Lab/Hypervisor", [T_HOST, "Linux by Zabbix agent active"], {
        # The standard template alerts on % used only (7.0): on this 278 GB disk 89.8 % used is still 28.9 GB
        # free (first false positive, 2026-11-02). Bytes are watched by Lab KVM host (HOST-01); the % triggers
        # stay as a last-resort backstop so the same condition does not page twice.
        "{$VFS.FS.PUSED.MAX.WARN}": "99", "{$VFS.FS.PUSED.MAX.CRIT}": "99.5",
    }),
    "db-orcl": ("Lab/Oracle", [T_DB], {"{$ORACLE.CONN}": "LAB_ORCL"}),
    "db-orcl-stb": ("Lab/Oracle", [T_DB], {"{$ORACLE.CONN}": "LAB_ORCL_STB", "{$BACKUP.HERE}": "1",
                                          # RAC backups are run by hand on the standby (offload), no timer
                                          "{$BACKUP.INCR.MAX.H}": "170", "{$BACKUP.ARCH.MAX.H}": "9999"}),
    "db-orcl3": ("Lab/Oracle", [T_DB], {"{$ORACLE.CONN}": "LAB_ORCL3", "{$BACKUP.HERE}": "1"}),
    "db-orcl3-stb": ("Lab/Oracle", [T_DB], {"{$ORACLE.CONN}": "LAB_ORCL3_STB"}),
}


def main():
    z = Zabbix.from_env()
    base = "file:///home/huy/work/noc-monitoring-incident-lab/04-runbooks"
    gm = z.call("usermacro.get", {"globalmacro": True, "filter": {"macro": "{$RUNBOOK.BASE}"}})
    if gm:
        z.call("usermacro.updateglobal", {"globalmacroid": gm[0]["globalmacroid"], "value": base})
    else:
        z.call("usermacro.createglobal", {"macro": "{$RUNBOOK.BASE}", "value": base,
                                          "description": "runbooks; GitHub URL once the repo is public"})
    z.call("housekeeping.update", {"hk_history_global": 1, "hk_history": "7d",
                                   "hk_trends_global": 1, "hk_trends": "90d"})
    for name in [GROUP_T]:
        if not z.call("templategroup.get", {"filter": {"name": name}}):
            z.call("templategroup.create", {"name": name})
    db, db_triggers = db_template()
    export = {"zabbix_export": {"version": "7.0", "template_groups": [{"uuid": uid("g", GROUP_T), "name": GROUP_T}],
                                "templates": [kvm_template(), db], "triggers": db_triggers}}
    rules = {k: {"createMissing": True, "updateExisting": True, "deleteMissing": True}
             for k in ["items", "triggers", "discoveryRules", "valueMaps", "templateDashboards", "httptests", "graphs"]}
    rules.update({"templates": {"createMissing": True, "updateExisting": True},
                  "template_groups": {"createMissing": True, "updateExisting": True},
                  "templateLinkage": {"createMissing": True}})
    z.call("configuration.import", {"format": "json", "rules": rules, "source": json.dumps(export)})

    for name in {g for g, _, _ in HOSTS.values()}:
        if not z.call("hostgroup.get", {"filter": {"name": name}}):
            z.call("hostgroup.create", {"name": name})
    for host, (group, templates, macros) in HOSTS.items():
        gid = z.call("hostgroup.get", {"filter": {"name": group}})[0]["groupid"]
        tids = [{"templateid": x["templateid"]} for x in
                z.call("template.get", {"filter": {"host": templates}, "output": ["templateid"]})]
        assert len(tids) == len(templates), f"{host}: template missing"
        body = {"groups": [{"groupid": gid}], "templates": tids,
                "macros": [{"macro": m, "value": v} for m, v in macros.items()]}
        old = z.call("host.get", {"filter": {"host": host}, "output": ["hostid"]})
        if old:
            z.call("host.update", {"hostid": old[0]["hostid"], **body})
        else:
            z.call("host.create", {"host": host, **body})
        print(f"{host}: {len(tids)} template(s), {len(macros)} macro(s)")

    # DG-07 (cross-host, so not in a template): a standby gap the KVM host cannot hold. Condition of the
    # 2026-11-02 02:58 incident (3.7 GB gap, ~3.5 GB free): enabling transport would fill the host.
    for host in ["db-orcl", "db-orcl-stb", "db-orcl3", "db-orcl3-stb"]:
        name = "{HOST.NAME}: redo gap {ITEM.LASTVALUE2} > host free space - 2 GB: do NOT enable transport"
        expr = (f'last(/{host}/lab.db.role)="PRIMARY" and '
                f"last(/{host}/lab.dg.dest.gap_mb)*1048576>last(/kvm-host/vfs.fs.size[/,free])-2147483648")
        body = {"description": name, "expression": expr, "priority": 4, "url": RUNBOOK + "DG-07-gap-vs-host.md",
                "url_name": "Runbook DG-07-gap-vs-host"}
        hid = z.call("host.get", {"filter": {"host": host}, "output": ["hostid"]})[0]["hostid"]
        old = [x for x in z.call("trigger.get", {"hostids": hid, "output": ["triggerid", "url"], "inherited": False})
               if x["url"].endswith("DG-07-gap-vs-host.md")]
        if old:
            z.call("trigger.update", {"triggerid": old[0]["triggerid"], **body})
        else:
            z.call("trigger.create", body)

    # the image's default host polls an agent at 127.0.0.1 inside the server container: keep only the
    # server's internal health template
    srv = z.call("host.get", {"filter": {"host": ["Zabbix server", "zabbix-server"]},
                              "output": ["hostid"], "selectParentTemplates": ["templateid", "host"]})
    if srv:
        drop = [t for t in srv[0]["parentTemplates"] if t["host"] != "Zabbix server health"]
        z.call("host.update", {"hostid": srv[0]["hostid"], "host": "zabbix-server",
                               "templates_clear": [{"templateid": t["templateid"]} for t in drop]})
    print("templates imported:", T_HOST, "/", T_DB, f"({len(db['items'])} items, {len(db_triggers)} triggers)")


if __name__ == "__main__":
    main()
