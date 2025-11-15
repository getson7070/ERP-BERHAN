# Local Docker bring-up (fixed)

## Prereqs
- Docker Desktop
- Ports 18000, 5432, 6379 free

## Steps
```bash
docker compose up --build
# then open http://localhost:18000/healthz
# to run migrations again (idempotent): docker compose exec web alembic upgrade head
# to run a shell: docker compose exec web python -c "from erp import create_app; print(create_app().url_map)"
```
