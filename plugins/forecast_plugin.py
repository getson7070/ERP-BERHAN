from flask import Blueprint, render_template

bp = Blueprint("forecast_plugin", __name__, url_prefix="/plugins/forecast")


@bp.route("/")
def index():
    data = [10, 12, 13]
    forecast = sum(data) / len(data)
    return render_template("plugins/forecast.html", forecast=forecast)


def register(app, registry):
    app.register_blueprint(bp)
    registry("forecast_plugin", bp=bp)
