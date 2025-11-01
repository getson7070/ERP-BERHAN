from flask import Blueprint
bp_demo = Blueprint("demo", __name__, url_prefix="/demo")

@bp_demo.get("/ping")
def ping():
    return "pong", 200
