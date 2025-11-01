from flask import Blueprint, render_template
bp = Blueprint("user_management", __name__, template_folder="../templates/user_management")
@bp.route("/")
def index():
    return render_template("user_management/index.html")
