# Migration <REVISION> — <TITLE>

## Purpose
- Why this migration exists
- Business reason

## Schema Changes
- Tables added/altered/dropped
- Columns added/removed/changed
- Indexes/constraints

## Data Backfill / Transform
- Any UPDATE/INSERT/normalization
- Expected row counts changed

## Expected Outcomes
- What must be true after upgrade
- Sample verification SQL:

```sql
-- example checks
SELECT count(*) FROM ...;
```

## Rollback Notes

* What downgrade does
* Any irreversible step

## Risks / Edge Cases

* Null handling
* multi-tenant org data
* large table lock expectations
