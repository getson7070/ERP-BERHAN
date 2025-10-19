# Zero-Downtime Migration Template (Expand → Backfill → Contract)

**Expand**: Add new columns/indexes with NULL allowed or defaults. Add new tables without dropping old paths.

**Backfill / Dual-Write**: Background job backfills new columns; app writes to both old and new fields during the window.

**Dual-Read**: App reads new fields first, fallback to old until cutover is verified.

**Contract**: Remove old columns/indexes after dashboards confirm parity; add NOT NULL / FK constraints last.

**CI Drill**: Run on ephemeral Postgres in CI with representative volumes; emit schema diff artifacts and require approval.
