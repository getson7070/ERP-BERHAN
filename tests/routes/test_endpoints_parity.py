import json, os
from erp import create_app

def test_template_endpoints_exist():
    app = create_app()
    report = json.load(open(os.path.join(os.getcwd(), "parity_report.json"), encoding="utf-8"))
    missing = report.get("endpoints_missing", {})
    assert sum(len(v) for v in missing.values()) == 0, f"Missing endpoints in templates: {list(missing.keys())[:5]}..."
