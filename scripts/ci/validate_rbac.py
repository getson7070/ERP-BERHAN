#!/usr/bin/env python3
import sys, yaml, json, os
path = "policy/rbac.yml"
with open(path, "r") as f:
    data = yaml.safe_load(f)

assert "roles" in data and isinstance(data["roles"], list), "rbac.yml must define a list of roles"
names = {r["name"] for r in data["roles"] if "name" in r}
assert names, "each role must have a name"
print("RBAC policy validated. Roles:", ", ".join(sorted(names)))
