from http import HTTPStatus

from erp import db
from erp.models import User
from erp.services.role_service import grant_role_to_user


def _login(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


def test_non_superadmin_cannot_grant_superadmin(app, client):
    app.config["LOGIN_DISABLED"] = False
    with app.app_context():
        admin = User(username="admin", email="admin@example.com")
        admin.password = "StrongPass123"
        target = User(username="target", email="t@example.com")
        target.password = "StrongPass123"
        db.session.add_all([admin, target])
        db.session.commit()

        grant_role_to_user(org_id=1, user_id=admin.id, role_key="admin", acting_user=None)

    _login(client, admin)
    resp = client.post(
        f"/api/admin/users/{target.id}/roles/grant",
        json={"role": "superadmin"},
    )
    assert resp.status_code in (HTTPStatus.FORBIDDEN, HTTPStatus.UNAUTHORIZED)
