from flask import Blueprint, current_app, render_template

bp = Blueprint('plugins', __name__, url_prefix='/plugins')

@bp.route('/')
def index():
    plugins = current_app.config.get('LOADED_PLUGINS', [])
    return render_template('plugins/index.html', plugins=plugins)
@bp.route("/marketplace")
def marketplace():
    plugins = current_app.config.get("PLUGIN_REGISTRY", [])
    return render_template("plugins/marketplace.html", plugins=plugins)

