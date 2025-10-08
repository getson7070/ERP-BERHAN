from flask import Blueprint, redirect, url_for, render_template, current_app

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    # Always show the nice chooser UI
    return redirect(url_for("main.choose_login"), code=302)

@bp.get("/choose-login")
def choose_login():
    # Render the template; if it’s missing, serve a tiny fallback so you never 500
    try:
        return render_template("choose-login.html")
    except Exception:
        current_app.logger.exception("choose-login.html missing; serving inline fallback.")
        return """
<!doctype html><title>Choose Login</title>
<h1>Choose Login</h1>
<p>Pick the portal you want to access.</p>
<p>
  <a href="/auth/login?role=admin">Admin</a> |
  <a href="/auth/login?role=employee">Employee</a> |
  <a href="/auth/login?role=client">Client</a>
</p>
""", 200

@bp.get("/healthz")
def healthz():
    return {"status": "ok"}, 200
