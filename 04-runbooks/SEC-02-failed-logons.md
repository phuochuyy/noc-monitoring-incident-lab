# SEC-02-failed-logons: ≥ 5 failed logons in 10 min (primary)

**Severity:** Warning

## Why it matters
Early warning before SEC-01, or password guessing. Empty user names are excluded (known standby internals, P2 finding 1b).

## Check
1. The audit query of SEC-01 (user, host, program).

## Fix
1. Known client with an old password: fix it. Unknown host/program: escalate.

## Escalate
Security owner for unknown sources.

## Close
Record the problem, cause and action in the shift log; if it repeats, open a problem record (root cause).
