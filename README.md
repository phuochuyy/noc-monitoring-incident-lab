# NOC Monitoring & Incident Response Lab

Monitoring an existing 8-VM Oracle lab (RAC, Data Guard, GoldenGate on KVM) the way a NOC shift does:
detect → ticket → handle or escalate → log → shift and monthly report.

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Zabbix 7.0 LTS (rootless Podman) on the KVM host; agent 2 on host and VMs; host disk, VM state, Oracle, Data Guard and GoldenGate items; time-to-detect measured against the old hourly health check | in progress |
| 2 | Alert → ticket (Jira Service Management), severity matrix, escalation | planned |
| 3 | Shift checklist every 8 h, handover and monthly reports, Grafana | planned |
| 4 | Fault-injection drills with runbooks and postmortems (MTTD / MTTR) | planned |
| 5 | Network / firewall segment (OPNsense, SNMP, syslog) | optional |

## Layout
- `01-stack/` — compose file and server configuration
- `02-agents/` — agent 2 configuration and install scripts for the host and the VMs
- `03-oracle/` — Oracle and GoldenGate checks (read-only user)
- `results/` — measurements and logs; `notes/worklog.md` — problems, causes, fixes
