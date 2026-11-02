#!/usr/bin/env bash
# Install the host agent as a systemd --user service (no root). Re-runnable.
# One-time root steps are printed, not run: stop the packaged agent, let the user service run without a login.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p ~/.config/systemd/user ~/.local/state/zabbix
install -m 644 "$here/zabbix-agent2.service" ~/.config/systemd/user/zabbix-agent2.service
/usr/sbin/zabbix_agent2 -c "$here/zabbix_agent2.conf" -T >/dev/null
systemctl --user daemon-reload
systemctl --user enable zabbix-agent2.service
systemctl --user restart zabbix-agent2.service
systemctl --user --no-pager --lines=0 status zabbix-agent2.service | head -3
if systemctl is-enabled zabbix-agent2.service >/dev/null 2>&1; then
  echo "root step: sudo systemctl disable --now zabbix-agent2   (packaged agent, not used)"
fi
if [ "$(loginctl show-user "$USER" -p Linger --value)" != yes ]; then
  echo "root step: sudo loginctl enable-linger $USER   (keep the agent running without a login session)"
fi
