from flask import Blueprint

bp = Blueprint("sample_plugin", __name__, url_prefix="/plugins/sample")


@bp.route("/")
def index():
    return "sample plugin"


def register(app, registry):
    app.register_blueprint(bp)
    registry("sample_plugin", bp=bp)


