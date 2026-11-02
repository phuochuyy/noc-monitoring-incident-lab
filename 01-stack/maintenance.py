"""Tell Zabbix which lab scenario is running (labctl.sh dg-a|dg-b|gg|rac|stop-all).

Databases the scenario stops on purpose go into one maintenance window (data still collected, problems
suppressed) - planned downtime is declared, not ignored. {$FSFO.EXPECTED} is set to 1 on the hosts of the
region that runs with Fast-Start Failover in that scenario. The KVM host is never put in maintenance.

usage: python3 maintenance.py <scenario>
"""
import sys
import time

from zbx import Zabbix

DB_HOSTS = ["db-orcl", "db-orcl-stb", "db-orcl3", "db-orcl3-stb"]
UP = {  # from labctl.sh: which databases each scenario starts
    "dg-a": {"db-orcl", "db-orcl-stb", "db-orcl3"},       # prm1 + stb1 + obs-r1 + prm3
    "dg-b": {"db-orcl3", "db-orcl3-stb", "db-orcl"},      # prm3 + stb3 + obs-r2 + prm1
    "gg": {"db-orcl", "db-orcl3"},                        # prm1 + prm3, Data Guard isolated
    "rac": {"db-orcl", "db-orcl3"},                       # prm1 + prm2 + prm3
    "stop-all": set(),
}
FSFO = {"dg-a": {"db-orcl", "db-orcl-stb"}, "dg-b": {"db-orcl3", "db-orcl3-stb"}}
NAME = "Lab scenario: databases stopped on purpose"


def set_macro(z, hostid, macro, value):
    m = z.call("usermacro.get", {"hostids": hostid, "filter": {"macro": macro}})
    if m:
        z.call("usermacro.update", {"hostmacroid": m[0]["hostmacroid"], "value": value})
    else:
        z.call("usermacro.create", {"hostid": hostid, "macro": macro, "value": value})


def main(scenario):
    if scenario not in UP:
        sys.exit(f"unknown scenario {scenario}; one of {', '.join(UP)}")
    z = Zabbix.from_env()
    hosts = {h["host"]: h["hostid"] for h in z.call("host.get", {"filter": {"host": DB_HOSTS}, "output": ["host"]})}
    for h, hid in hosts.items():
        set_macro(z, hid, "{$FSFO.EXPECTED}", "1" if h in FSFO.get(scenario, set()) else "0")
    for m in z.call("maintenance.get", {"filter": {"name": NAME}}):
        z.call("maintenance.delete", [m["maintenanceid"]])
    down = [h for h in DB_HOSTS if h not in UP[scenario]]
    if down:
        now = int(time.time())
        z.call("maintenance.create", {
            "name": NAME, "maintenance_type": 0, "active_since": now - 60, "active_till": now + 365 * 86400,
            "description": f"set by maintenance.py {scenario}",
            "hosts": [{"hostid": hosts[h]} for h in down],
            "timeperiods": [{"timeperiod_type": 0, "start_date": now - 60, "period": 365 * 86400}]})
    print(f"{scenario}: up {sorted(UP[scenario]) or '-'}; maintenance {down or '-'}; "
          f"FSFO expected {sorted(FSFO.get(scenario, set())) or '-'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
