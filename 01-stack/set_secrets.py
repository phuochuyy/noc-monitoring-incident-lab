"""Copy the C##MON password from the Ansible Vault of oracle-dba-automation-cdc into Zabbix as a global
*secret* macro {$ORACLE.PASSWORD} (type 1: write-only in the UI and API). Nothing is printed or written to disk.

usage: ~/work/tools/venvs/dba/bin/python set_secrets.py
"""
import pathlib
import subprocess
import sys

import yaml  # in the dba venv (ansible-core)

from zbx import Zabbix

REPO = pathlib.Path.home() / "work/oracle-dba-automation-cdc"
VAULT = REPO / "01-ansible/group_vars/all/vault.yml"
PASS_FILE = pathlib.Path.home() / ".vault_pass_dba"

out = subprocess.run([str(pathlib.Path(sys.executable).parent / "ansible-vault"), "view",
                      "--vault-password-file", str(PASS_FILE), str(VAULT)],
                     check=True, capture_output=True, text=True).stdout
pw = yaml.safe_load(out)["vault_user_passwords"]["c##mon"]

z = Zabbix.from_env()
macro = "{$ORACLE.PASSWORD}"
old = z.call("usermacro.get", {"globalmacro": True, "filter": {"macro": macro}})
body = {"value": pw, "type": 1, "description": "C##MON (read-only), from the Ansible Vault of P3"}
if old:
    z.call("usermacro.updateglobal", {"globalmacroid": old[0]["globalmacroid"], **body})
else:
    z.call("usermacro.createglobal", {"macro": macro, **body})
print(f"{macro} set (secret, {len(pw)} characters)")
