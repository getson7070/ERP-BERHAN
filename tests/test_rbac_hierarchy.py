from flask import Flask, Blueprint, session
from erp.utils import roles_required


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "test"
    main = Blueprint("main", __name__)

    @main.route("/dashboard")
    def dashboard():
        return "dashboard"

    app.register_blueprint(main)

    @app.route("/manager")
    @roles_required("Manager")
    def manager():
        return "ok"

    return app


app = create_app()
manager_view = app.view_functions["manager"]


def test_admin_inherits_manager():
    with app.test_request_context("/manager"):
        session["role"] = "Admin"
        assert manager_view() == "ok"


def test_staff_denied_manager():
    with app.test_request_context("/manager"):
        session["role"] = "Staff"
        resp = manager_view()
        assert resp.status_code == 302


