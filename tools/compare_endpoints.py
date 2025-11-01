# tools/compare_endpoints.py
import json, sys
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
sa = {(x["endpoint"], x["rule"]) for x in a}
sb = {(x["endpoint"], x["rule"]) for x in b}
print("Removed:", sorted(sa - sb))
print("Added  :", sorted(sb - sa))
