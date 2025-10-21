from flask import Blueprint, render_template
from erp.utils import login_required

bp = Blueprint("kanban", __name__, url_prefix="/kanban")


@bp.route("/", methods=["GET"])
@login_required
def board():
    tasks = {
        "todo": ["Draft proposal", "Collect requirements"],
        "in_progress": ["Implement feature"],
        "done": ["Initial setup"],
    }
    return render_template("kanban_board.html", tasks=tasks)


