import os, re, pathlib, sys

ROOT = pathlib.Path(os.getcwd())
py_files = list(ROOT.rglob("*.py"))
templates = set()
for p in ROOT.rglob("templates"):
    for f in p.rglob("*"):
        if f.suffix.lower() in (".html",".jinja",".jinja2"):
            rel = f.relative_to(p)
            templates.add(str(rel).replace("\\","/"))

missing = []
for py in py_files:
    txt = py.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'render_template\(\s*['"]([^'"]+)['"]', txt):
        t = m.group(1)
        if t not in templates:
            missing.append((str(py), t))
for path, t in missing:
    print(f"[missing-template] {path} -> {t}")
if not missing:
    print("[ok] All render_template() calls have corresponding files.")
