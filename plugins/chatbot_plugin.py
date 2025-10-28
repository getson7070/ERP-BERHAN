from flask import Blueprint, request, jsonify

bp = Blueprint("chatbot_plugin", __name__, url_prefix="/plugins/chatbot")


@bp.route("/echo")
def echo():
    msg = request.args.get("msg", "")
    return jsonify({"reply": msg})


def register(app, registry):
    app.register_blueprint(bp)

    def chatbot_hook(message: str) -> str:
        return f"echo: {message}"

    registry("chatbot_plugin", bp=bp, chatbot=chatbot_hook)


