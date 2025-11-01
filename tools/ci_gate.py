import os, subprocess, sys
from typing import Optional
from alembic.config import Config
from alembic.script import ScriptDirectory

def load_cfg():
    for cand in ("alembic.ini", "migrations/alembic.ini"):
        if os.path.exists(cand):
            return Config(cand)
    cfg = Config()
    cfg.set_main_option("script_location", os.getenv("ALEMBIC_SCRIPT_LOCATION", "migrations"))
    return cfg

def check_heads()->int:
    script = ScriptDirectory.from_config(load_cfg())
    heads = script.get_heads()
    print(f"[CHECK] Alembic heads: {heads}")
    return 1 if len(heads)==1 else 0

def upgrade()->int:
    p = subprocess.run(["alembic","upgrade","head"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ok = p.returncode==0
    print("[CHECK] Upgrade to head:", "OK" if ok else "FAIL")
    if not ok: print(p.stdout)
    return 1 if ok else 0

def resolve_app():
    os.environ.setdefault("FLASK_APP","erp.boot:create_app")
    try:
        from flask.cli import ScriptInfo
        return ScriptInfo(create_app=None).load_app()
    except Exception:
        pass
    # Fallback candidates
    for mod, obj in [("erp.boot","create_app"),("erp","create_app"),("app","create_app"),("server","create_app")]:
        try:
            m = __import__(mod, fromlist=[obj])
            f = getattr(m, obj, None)
            if callable(f): return f()
            app = getattr(m,"app",None) or getattr(m,"application",None)
            if app is not None: return app
        except Exception:
            continue
    return None

def blueprints()->int:
    app = resolve_app()
    if app is None:
        print("[CHECK] Blueprints: FAIL (cannot resolve Flask app)")
        return 0
    bps = sorted(app.blueprints.items())
    print(f"[CHECK] Blueprints registered: {len(bps)}")
    for name, bp in bps:
        print(f" - {name} prefix={bp.url_prefix!r}")
    # Succeed if at least one blueprint is registered; adjust if you want stricter policy
    return 1 if len(bps)>=1 else 0

def main():
    score=0; total=3
    score+=check_heads()
    score+=upgrade()
    score+=blueprints()
    print(f"SCORE: {score}/{total}")
    sys.exit(0 if score==total else 1)

if __name__=="__main__":
    main()
