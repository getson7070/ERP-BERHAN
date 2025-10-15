# scripts/migrations/print_heads.py
import subprocess, sys
def run(*args):
    p = subprocess.run(args, text=True, capture_output=True)
    print(f"$ {' '.join(args)}\n{(p.stdout or '') + (p.stderr or '')}")
print("Alembic diagnostics:")
run("alembic", "-c", "alembic.ini", "heads", "-q")
run("alembic", "-c", "alembic.ini", "heads", "--verbose")
run("alembic", "-c", "alembic.ini", "branches")
run("alembic", "-c", "alembic.ini", "history", "--verbose")
