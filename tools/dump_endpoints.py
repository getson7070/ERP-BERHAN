from collections import defaultdict
import json
from erp import create_app

app = create_app()
with app.app_context():
    rules = []
    for r in app.url_map.iter_rules():
        rules.append({"endpoint": r.endpoint, "rule": str(r), "methods": sorted(r.methods)})
    rules_sorted = sorted(rules, key=lambda x: (x["endpoint"], x["rule"]))
    print("TOTAL ENDPOINTS:", len(rules_sorted))
    with open("endpoints_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(rules_sorted, f, indent=2)
    print("Wrote endpoints_snapshot.json")
