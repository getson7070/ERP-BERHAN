# tools/check_templates.py
import os, re, sys, pathlib

APP = pathlib.Path(".")
TEMPLATES = APP / "templates"

route_re = re.compile(r"@\w+\.route\(['\"]([^'\"]+)['\"][^)]*\)")
render_re = re.compile(r"render_template\(['\"]([^'\"]+)['\"]")
jinja_exts = {".html", ".jinja", ".jinja2"}

routes = set()
renders = set()
missing = []

for py in APP.rglob("*.py"):
    if "venv" in py.parts or ".venv" in py.parts or "migrations" in py.parts:
        continue
    txt = py.read_text(errors="ignore")
    for m in route_re.finditer(txt):
        routes.add(m.group(1))
    for m in render_re.finditer(txt):
        renders.add(m.group(1))

for tpl in renders:
    exists = any((TEMPLATES / tpl).exists() or (TEMPLATES / (tpl + ext)).exists() for ext in [""])
    if not exists:
        missing.append(tpl)

print("Routes found:", len(routes))
print("Templates referenced:", len(renders))
if missing:
    print("\nMissing templates:")
    for m in sorted(set(missing)):
        print(" -", m)
    sys.exit(2)
else:
    print("All referenced templates exist.")
