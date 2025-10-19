#!/usr/bin/env python3
import sys, yaml, re
from importlib import import_module

# Attempt common entrypoints
def load_app():
    for mod, attr in [
        ("erp", "app"), ("erp.app", "app"),
        ("erp", "create_app"), ("erp.app", "create_app"),
    ]:
        try:
            m = import_module(mod)
            if hasattr(m, attr):
                obj = getattr(m, attr)
                return obj() if callable(obj) else obj
        except Exception:
            continue
    print("ERROR: Could not import Flask app (tried erp.app/app/create_app).", file=sys.stderr)
    sys.exit(2)

def load_policy():
    with open("policy/rbac.yml", "r") as f:
        return yaml.safe_load(f)

def covered(route, methods, policy):
    for role_def in policy.get("roles", {}).values():
        for ep in role_def.get("endpoints", []):
            path = ep["path"]
            match = ep.get("match", "prefix")
            if (match == "exact" and route == path) or (match == "prefix" and route.startswith(path)):
                if set(methods) & set(ep.get("methods", [])):
                    return True
    return False

def main():
    app = load_app()
    pol = load_policy()
    # ignore framework internals
    skip = re.compile(r"^/(static|_debug_toolbar|favicon\.ico)")
    drift = []
    for rule in app.url_map.iter_rules():
        path = str(rule)
        if skip.match(path):
            continue
        meth = [m for m in rule.methods if m in {"GET","POST","PUT","DELETE","PATCH"}]
        if not covered(path, meth, pol):
            drift.append((path, meth))
    if drift:
        print("RBAC drift detected for routes:")
        for p, ms in sorted(drift):
            print(f"  {p}  methods={','.join(ms)}")
        sys.exit(1)
    print("RBAC linter: OK")
    sys.exit(0)

if __name__ == "__main__":
    main()
