# Incident Response

## Severity Levels
- S1: Full outage / data corruption
- S2: One critical module down (inventory/finance/ordering)
- S3: External dependency down (banking/telegram) but ERP core OK

## Immediate Actions
1. Confirm scope via `/healthz` and dashboards.
2. If S1/S2:
   - freeze changes
   - notify leadership
3. Retrieve last 24h logs + bot events.
4. Identify breaker-open incidents (`/api/reliability/mttr` for history).

## Stabilize
- Disable failing integration via ENV toggle
  - `BANKING_ENABLED=0`
  - `TELEGRAM_ENABLED=0`
- Scale worker if backlog > threshold.

## Recover
- Patch hotfix branch
- Run CI + chaos suite
- Deploy
- Close incident

## Postmortem
- Root cause
- What failed to detect earlier
- New alert needed
- MTTR recorded
