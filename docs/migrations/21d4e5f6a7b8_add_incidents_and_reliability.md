# Migration 21d4e5f6a7b8 — Add incidents table for reliability tracking

## Purpose
- Introduces an `incidents` table to record outages and recovery events for MTTR reporting and circuit-breaker integrations.

## Schema Changes
- Added table `incidents` with org, service, status, timestamps, and detail payload.
- Indexes on `org_id`, `service`, and `status` for fast querying.

## Data Backfill / Transform
- No backfill required; table starts empty.

## Expected Outcomes
- `incidents` table exists and can store open/recovered incidents.
- Example verification:

```sql
SELECT column_name FROM information_schema.columns WHERE table_name='incidents';
```

## Rollback Notes
- Downgrade drops the `incidents` table and its data.

## Risks / Edge Cases
- Ensure migrations run during a maintenance window if incident data is already being collected in another system.
