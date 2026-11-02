#!/usr/bin/env bash
# Thin-provisioning headroom of the KVM host, as JSON for a Zabbix master item.
#   apparent  = what the sparse VM disk images are allowed to grow to (bytes)
#   allocated = what they really use on the host file system
#   growth    = apparent - allocated (how much the guests can still write)
#   fs_free   = free bytes of the file system holding the images
#   cover_pct = fs_free / growth * 100 (below 100 % the host cannot hold all the growth it promised)
set -euo pipefail
dir=${1:-/opt/lab/oracle-rac}
apparent=$(du -s --apparent-size -B1 "$dir" | cut -f1)
allocated=$(du -s -B1 "$dir" | cut -f1)
free=$(df -B1 --output=avail "$dir" | tail -1 | tr -d ' ')
growth=$(( apparent > allocated ? apparent - allocated : 0 ))
cover=$(awk -v f="$free" -v g="$growth" 'BEGIN{ if (g==0) print 100; else printf "%.1f", f/g*100 }')
printf '{"apparent":%s,"allocated":%s,"growth":%s,"fs_free":%s,"cover_pct":%s}\n' \
  "$apparent" "$allocated" "$growth" "$free" "$cover"
