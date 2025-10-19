#!/usr/bin/env python3
import sys, yaml, re
from importlib import import_module

def load_app():
    candidates = [("erp", "app"), ("erp.app", "app"), ("erp", "create_app"), ("erp.app", "create_app")]
    for mod, attr in candidates:
        try:
            m = import_module(mod)
            obj = getattr(m, attr, None)
            if obj is None:
                continue
            return obj() if callable(obj) else obj
        except Exception:
            continue
    print("ERROR: Could not import Flask app from any known entrypoint.", file=sys.stderr)
    sys.exit(2)

def load_policy():
    with open("policy/rbac.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def covered(route, methods, policy):
    for role_def in policy.get("roles", {}).values():
        for ep in role_def.get("endpoints", []):
            path = ep["path"]
            match = ep.get("match", "prefix")
            method_set = set(ep.get("methods", []))
            if (match == "exact" and route == path) or (match == "prefix" and route.startswith(path)):
                if method_set & set(methods):
                    return True
    return False

def main():
    try:
        import yaml  # ensure dependency present
    except Exception:
        print("pyyaml not installed. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(2)

    app = load_app()
    policy = load_policy()

    skip = re.compile(r"^/(static|_debug_toolbar|favicon\.ico)")
    drift = []
    for rule in app.url_map.iter_rules():
        path = str(rule)
        if skip.match(path):
            continue
        methods = [m for m in rule.methods if m in {"GET","POST","PUT","DELETE","PATCH"}]
        if not methods:
            continue
        if not covered(path, methods, policy):
            drift.append((path, methods))

    if drift:
        print("RBAC drift detected for routes:")
        for p, ms in sorted(drift):
            print(f"  {p}  methods={','.join(ms)}")
        sys.exit(1)
    print("RBAC linter: OK")
    sys.exit(0)

if __name__ == "__main__":
    main()
