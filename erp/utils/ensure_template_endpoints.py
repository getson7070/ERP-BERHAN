import os, re, glob, functools
from flask import abort

def _discover_template_endpoints(app_root):
    # Correct pattern: url_for('<endpoint.name>')
    pat = re.compile(r"url_for\(\s*['\"]([\w\.]+)['\"]")
    root = os.path.join(app_root, "templates")
    found = set()
    for p in glob.glob(os.path.join(root, "**", "*.html"), recursive=True):
        try:
            txt = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for ep in pat.findall(txt):
            found.add(ep)
    return found

def install_dev_stubs_for_missing_template_endpoints(app):
    """
    Dev-only safety net:
      - Scan templates for url_for('endpoint')
      - If endpoint not registered, install a stub that returns 501
    Enable via ERP_STUB_MISSING_ENDPOINTS=1 (default in dev).
    """
    if os.getenv("ERP_STUB_MISSING_ENDPOINTS", "1") not in ("1", "true", "True"):
        return

    template_eps = _discover_template_endpoints(app.root_path)
    existing = set(app.view_functions.keys())
    missing = sorted(ep for ep in template_eps if ep not in existing)

    for ep in missing:
        rule = f"/__missing/{ep.replace('.', '/')}"
        def _stub(ep_name):
            @functools.wraps(_stub)
            def _handler():
                abort(501, description=f'Endpoint "{ep_name}" is referenced in templates but not implemented.')
            return _handler
        try:
            app.add_url_rule(rule, endpoint=ep, view_func=_stub(ep))
        except Exception:
            # If a blueprint later defines the same endpoint, ignore collision here
            pass