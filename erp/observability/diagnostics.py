from flask import Blueprint, current_app, render_template, jsonify

diagnostics_bp = Blueprint("diagnostics", __name__, template_folder="../templates")

@diagnostics_bp.get("/diagnostics")
def diagnostics():
    failures = current_app.config.get("IMPORT_FAILURES", [])
    bps = current_app.config.get("REGISTERED_BLUEPRINTS", [])
    return render_template("admin/diagnostics.html", failures=failures, blueprints=bps)

@diagnostics_bp.get("/blueprints")
def blueprints():
    return jsonify(current_app.config.get("REGISTERED_BLUEPRINTS", []))

@diagnostics_bp.get("/import_failures")
def import_failures():
    return jsonify(current_app.config.get("IMPORT_FAILURES", []))
