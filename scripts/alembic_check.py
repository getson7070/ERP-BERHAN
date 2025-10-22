
import sys
from pathlib import Path

def main():
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
    except Exception as e:
        print("[WARN] Alembic not installed; skipping single-head check.")
        sys.exit(0)

    ini = Path("alembic.ini")
    if not ini.exists():
        print("[WARN] alembic.ini not found; skipping single-head check.")
        sys.exit(0)

    cfg = Config(str(ini))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    if len(heads) != 1:
        print(f"[ERROR] Alembic has {len(heads)} heads: {heads}. Please converge into a single head.")
        sys.exit(1)
    print("[OK] Alembic single head confirmed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
