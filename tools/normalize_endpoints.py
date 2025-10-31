# tools/normalize_endpoints.py
import os, re, sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "erp", "templates")
M = {
    r"\burl_for\(\s*'health\.health'\s*\)":             "url_for('health_bp.health')",
    r'\burl_for\(\s*"health\.health"\s*\)':             'url_for("health_bp.health")',
    r"\burl_for\(\s*'auth\.choose_login'\s*\)":         "url_for('auth.login')",
    r'\burl_for\(\s*"auth\.choose_login"\s*\)':         'url_for("auth.login")',
    r"\burl_for\(\s*'tenders\.tenders_list'\s*\)":      "url_for('projects.index')",
    r'\burl_for\(\s*"tenders\.tenders_list"\s*\)':      'url_for("projects.index")',
    r"\burl_for\(\s*'user_management\.approve_client'\s*\)": "url_for('crm.index')",
    r'\burl_for\(\s*"user_management\.approve_client"\s*\)': 'url_for("crm.index")',
    r"\burl_for\(\s*'user_management\.create_employee'\s*\)": "url_for('hr.index')",
    r'\burl_for\(\s*"user_management\.create_employee"\s*\)': 'url_for("hr.index")',
    r"\burl_for\(\s*'user_management\.edit_user'\s*\)": "url_for('hr.index')",
    r'\burl_for\(\s*"user_management\.edit_user"\s*\)': 'url_for("hr.index")',
    r"\burl_for\(\s*'user_management\.delete_user'\s*\)": "url_for('hr.index')",
    r'\burl_for\(\s*"user_management\.delete_user"\s*\)': 'url_for("hr.index")',
    r"\burl_for\(\s*'user_management\.reject_client'\s*\)": "url_for('crm.index')",
    r'\burl_for\(\s*"user_management\.reject_client"\s*\)': 'url_for("crm.index")',
}

patts = [(re.compile(k), v) for k, v in M.items()]

changed = 0
for root, _, files in os.walk(ROOT):
    for f in files:
        if not f.endswith(".html"): continue
        p = os.path.join(root, f)
        txt = open(p, encoding="utf-8", errors="ignore").read()
        orig = txt
        for rx, repl in patts:
            txt = rx.sub(repl, txt)
        if txt != orig:
            open(p, "w", encoding="utf-8").write(txt)
            changed += 1
            print("updated:", os.path.relpath(p, ROOT))

print("files_changed:", changed)
