import os
from flask.cli import ScriptInfo
os.environ.setdefault("FLASK_APP","erp.boot:create_app")
app = ScriptInfo(create_app=None).load_app()
print("=== Blueprints ===")
for n,bp in sorted(app.blueprints.items()):
    print(f"{n:25s} prefix={bp.url_prefix!r}")
print("=== URL Map ===")
for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods=",".join(sorted(m for m in r.methods if m not in {"HEAD","OPTIONS"}))
    print(f"{methods:10s} {r.rule:40s} -> {r.endpoint}")
