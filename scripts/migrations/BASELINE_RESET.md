# Migration Baseline Reset (Recommended)

Your repo has multiple Alembic heads and malformed revisions. To reach **1 head**, do this on a **staging** DB:

```bash
# 0) Backup your DB first!

# 1) Archive old migrations
mkdir -p migrations/_archive_2025-10-13
git mv migrations/versions migrations/_archive_2025-10-13 || mv migrations/versions migrations/_archive_2025-10-13
mkdir -p migrations/versions

# 2) Generate a fresh baseline from current models
alembic revision --autogenerate -m "baseline 2025-10-13"

# 3) Upgrade
alembic upgrade head
```

If you must preserve history, repair to a single head:
```bash
alembic heads
# Make or edit merge revisions to reduce to ONE head
# Fix any files missing 'revision' or 'down_revision'
alembic upgrade head
```
