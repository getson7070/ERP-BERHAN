# scripts/migrations/print_heads.py
import subprocess
print(subprocess.check_output(["alembic", "-c", "alembic.ini", "heads"]).decode())
