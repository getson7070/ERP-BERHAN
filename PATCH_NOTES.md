# ERP-BERHAN — Phase 1 (Very Critical) Patch
Date: 2025-10-24

This drops in **surgical, compatibility-safe** files to unblock deploys and remove reliability foot‑guns:
- **Root `db.py`**: consistent SQLAlchemy connection from `DATABASE_URL` + resilient Redis client **with `get`/`set`** used by idempotency, MFA, and dead-letter logic.
- **`erp/__init__.py`**: single app factory; late-binds extensions; **safe blueprint auto‑discovery**; minimal security headers; health/metrics ready for probes.
- **`erp/extensions.py`**: robust `csrf`, `limiter`, `login_manager`, and `db` import shim.
- **`migrations/env.py`**: Alembic decoupled from app import; uses metadata from `erp.extensions.db`.
- **`gunicorn.conf.py`** + **`wsgi_eventlet.py`**: production server defaults & async option; plays well with Render/App Runner.
- **Scripts**: `run_migrations.sh`, `rotate_jwt_secret.py` with clear, idempotent steps.
- **`.env.example`** additions for required secrets and rate‑limit storage.

These changes are **intra‑module aware**: they keep import graphs acyclic, avoid decorator evaluation before extension init, and maintain compatibility with existing tests and routes. 
