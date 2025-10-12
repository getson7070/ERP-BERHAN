# scripts/guard_create_tables.py
import re, pathlib

root = pathlib.Path("migrations/versions")
for f in root.glob("*.py"):
    src = f.read_text(encoding="utf-8", errors="ignore")
    # only touch files with create_table and no existing inspect() guard
    if "op.create_table(" not in src or "inspect(" in src:
        continue

    if "import sqlalchemy as sa" not in src:
        src = src.replace("from alembic import op", "from alembic import op\nimport sqlalchemy as sa")

    # ensure we have 'bind' and 'insp'
    if "sa.inspect(" not in src:
        src = src.replace("def upgrade():", "def upgrade():\n    bind = op.get_bind()\n    insp = sa.inspect(bind)")

    # wrap each op.create_table('table_name', ...) in a guard
    def repl(m):
        table = m.group(1)
        body  = m.group(0)
        return f"if not insp.has_table({table}, schema='public'):\n        {body}"

    # crude but effective: only matches simple string literal first arg
    src = re.sub(r"op\.create_table\(\s*('(?:[^']|\\')+'|\"(?:[^\"]|\\\")+\")\s*,", repl, src)

    f.write_text(src, encoding="utf-8")
    print("guarded:", f)
