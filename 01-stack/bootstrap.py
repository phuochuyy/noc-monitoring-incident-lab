"""One-time: replace the default Admin password (zabbix) with ZBX_ADMIN_PASSWORD from ../lab.env.

Safe to re-run: if the default password no longer works, it only checks that the new one does.
"""
import sys

from zbx import Zabbix, ZabbixError, load_env

env = load_env()
new = env["ZBX_ADMIN_PASSWORD"]
try:
    z = Zabbix().login("Admin", "zabbix")
except ZabbixError:
    Zabbix().login("Admin", new)
    print("default password already replaced; new password works")
    sys.exit(0)

uid = z.call("user.get", {"filter": {"username": "Admin"}, "output": ["userid"]})[0]["userid"]
z.call("user.update", {"userid": uid, "current_passwd": "zabbix", "passwd": new})
Zabbix().login("Admin", new)
print("Admin password replaced; login with the new password OK")
