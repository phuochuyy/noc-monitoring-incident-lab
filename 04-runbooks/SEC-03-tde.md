# SEC-03-tde: TDE keystore not open

**Severity:** High

## Why it matters
Encrypted tablespaces (SECPDB, DRILLPDB, ORCLPDB2.APP_DATA, PERF.BANK_DATA) cannot be read; on a standby, redo apply stops at the next encrypted change.

## Check
1. `select con_id, status, wallet_type from v$encryption_wallet`
1. WALLET_ROOT and the files `ewallet.p12` / `cwallet.sso`.

## Fix
1. Auto-login keystore: check the `cwallet.sso` file; standby: copy both files from the primary (same md5), then restart apply.

## Escalate
Security owner; never re-create a keystore (data would be lost).

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
