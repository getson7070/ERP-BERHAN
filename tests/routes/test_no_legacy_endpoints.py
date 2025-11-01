# tests/routes/test_no_legacy_endpoints.py
import json, os
from erp import create_app

LEGACY = {
    "auth.choose_login",
    "health.health",
    "hr.add_employee",
    "login_ui.logout",
    "tenders.tenders_list",
    "user_management.approve_client",
    "user_management.create_employee",
    "user_management.edit_user",
    "user_management.delete_user",
    "user_management.reject_client",
}

def test_no_legacy_endpoints_present():
    app = create_app()
    with app.app_context():
        eps = set(app.view_functions.keys())
    # Legacy may be present in views only through shims; we enforce *template* usage is canonical.
    assert not (LEGACY & eps), f"Legacy endpoints present: {sorted(LEGACY & eps)}"
