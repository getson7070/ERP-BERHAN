import os, re, sys, pathlib
APP = pathlib.Path(".")
TEMPLATES = APP / "templates"

render_re = re.compile(r"render_template\(['"]([^'"]+)['"]")
missing = []

renders = set()
for py in APP.rglob("*.py"):
    if any(x in py.parts for x in (".venv","venv","migrations","tests","site-packages")):
        continue
    try:
        txt = py.read_text(errors="ignore")
    except Exception:
        continue
    for m in render_re.finditer(txt):
        renders.add(m.group(1))

for tpl in renders:
    if not (TEMPLATES / tpl).exists():
        missing.append(tpl)

print("Templates referenced:", len(renders))
if missing:
    print("\nMissing templates:")
    for m in sorted(set(missing)):
        print(" -", m)
    sys.exit(2)
else:
    print("All referenced templates exist.")
