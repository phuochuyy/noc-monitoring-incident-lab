"""Time-to-detect / time-to-resolve drills against the Zabbix pipeline.

A drill injects a fault at T0, polls Zabbix (API) for the problem of the expected trigger, then removes the
fault at T2 and waits for the problem to resolve. Times come from Zabbix event clocks (problem start = event
clock, resolution = r_clock), not from the poll loop.

Drills
  d1-disk   raise {$HOST.FREE.WARN} on kvm-host above the current free space (Zabbix config only, no VM
            touched), then restore it. Exercises: macro sync -> next 1-min value -> trigger -> problem.

usage: python3 mttd.py d1-disk [runs] [label]     -> appends to ../results/phase1-mttd-<label>.log and .jsonl
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "01-stack"))
from zbx import Zabbix  # noqa: E402

RESULTS = pathlib.Path(__file__).resolve().parent.parent / "results"


def ts(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def host_macro(z, host, macro):
    hid = z.call("host.get", {"filter": {"host": host}, "output": ["hostid"]})[0]["hostid"]
    m = z.call("usermacro.get", {"hostids": hid, "filter": {"macro": macro}})
    return hid, (m[0] if m else None)


def set_host_macro(z, host, macro, value):
    hid, m = host_macro(z, host, macro)
    if value is None:
        if m:
            z.call("usermacro.delete", [m["hostmacroid"]])
    elif m:
        z.call("usermacro.update", {"hostmacroid": m["hostmacroid"], "value": value})
    else:
        z.call("usermacro.create", {"hostid": hid, "macro": macro, "value": value})


def trigger_id(z, host, url_suffix, name_part):
    hid = z.call("host.get", {"filter": {"host": host}, "output": ["hostid"]})[0]["hostid"]
    for t in z.call("trigger.get", {"hostids": hid, "output": ["triggerid", "description", "url"]}):
        if t["url"].endswith(url_suffix) and name_part in t["description"]:
            return t["triggerid"]
    raise SystemExit(f"trigger {url_suffix} / {name_part} not found on {host}")


def wait_event(z, triggerid, since, value, timeout):
    """First event of the trigger with clock >= since and the given value (1 problem, 0 OK)."""
    end = time.time() + timeout
    while time.time() < end:
        ev = z.call("event.get", {"objectids": triggerid, "source": 0, "object": 0, "value": value,
                                  "time_from": int(since), "output": ["eventid", "clock", "name"],
                                  "sortfield": ["clock"], "sortorder": "ASC", "limit": 1})
        if ev:
            return ev[0]
        time.sleep(2)
    return None


def d1_disk(z):
    host, macro = "kvm-host", "{$HOST.FREE.WARN}"
    tid = trigger_id(z, host, "HOST-01-disk.md", "/ free {ITEM.LASTVALUE} < {$HOST.FREE.WARN}")
    hid = z.call("host.get", {"filter": {"host": host}, "output": ["hostid"]})[0]["hostid"]
    free = int(z.call("item.get", {"hostids": hid, "filter": {"key_": "vfs.fs.size[/,free]"},
                                   "output": ["lastvalue"]})[0]["lastvalue"])
    inject = f"{free // 2**30 + 10}G"          # 10 GB above what is free now
    _, old = host_macro(z, host, macro)
    old_value = old["value"] if old else None   # normally unset on the host: template value 12G applies
    t0 = time.time()
    set_host_macro(z, host, macro, inject)
    p = wait_event(z, tid, t0 - 1, 1, 300)
    t2 = time.time()
    set_host_macro(z, host, macro, old_value)
    r = wait_event(z, tid, t2 - 1, 0, 300)
    return {"drill": "d1-disk", "fault": f"{macro} {old_value or 'template 12G'} -> {inject} (free {free / 2**30:.1f} GiB)",
            "t0": ts(t0), "problem": ts(int(p["clock"])) if p else None,
            "detect_s": round(int(p["clock"]) - t0, 1) if p else None,
            "t2_restore": ts(t2), "resolved": ts(int(r["clock"])) if r else None,
            "resolve_s": round(int(r["clock"]) - t2, 1) if r else None,
            "problem_name": p["name"] if p else None}


DRILLS = {"d1-disk": d1_disk}


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    label = sys.argv[3] if len(sys.argv) > 3 else "r1"
    if name not in DRILLS:
        sys.exit(f"usage: mttd.py <{'|'.join(DRILLS)}> [runs] [label]")
    z = Zabbix.from_env()
    RESULTS.mkdir(exist_ok=True)
    log, jl = RESULTS / f"phase1-mttd-{label}.log", RESULTS / f"phase1-mttd-{label}.jsonl"
    for i in range(1, runs + 1):
        res = DRILLS[name](z) | {"run": i}
        line = (f"{res['drill']} run {i}: fault {res['t0']} | problem {res['problem']} (+{res['detect_s']} s) | "
                f"restored {res['t2_restore']} | resolved {res['resolved']} (+{res['resolve_s']} s) | {res['fault']}")
        print(line)
        with log.open("a") as f:
            f.write(line + "\n")
        with jl.open("a") as f:
            f.write(json.dumps(res) + "\n")
        time.sleep(20)


if __name__ == "__main__":
    main()
