import os
from erp import create_app
if "testing" in create_app.__code__.co_varnames:
    app = create_app(testing=False)
else:
    app = create_app()

@app.get("/")
def root():
    return {
        "ok": True,
        "app": "ERP-BERHAN",
        "endpoints": ["/status", "/ops/doctor"]
    }