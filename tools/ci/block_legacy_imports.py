import pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
bad = re.compile(r"\bfrom\s+erp\.crm\.extensions\b")

violations = []
for p in REPO.rglob("*.py"):
    if p.is_file():
        t = p.read_text(encoding="utf-8", errors="ignore")
        if bad.search(t):
            violations.append(str(p.relative_to(REPO)))

if violations:
    print("ERROR: legacy imports found (use `from erp.extensions import db`):")
    for v in violations:
        print(" -", v)
    sys.exit(1)
print("OK: no legacy crm.extensions imports.")
