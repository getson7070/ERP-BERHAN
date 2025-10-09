from flask import Blueprint, render_template, redirect

bp = Blueprint("main", __name__)

@bp.get("/")
def root():
    # Keep your original redirect behavior to role chooser
    return redirect("/choose_login", code=302)

@bp.get("/choose_login")
def choose_login():
    # Purely public page; relies on safety user_loader so it never 500s
    roles = [
        {"key": "admin", "label": "Admin"},
        {"key": "sales", "label": "Sales"},
        {"key": "store", "label": "Storekeeper"},
        {"key": "finance", "label": "Finance"},
        {"key": "tech", "label": "Technical"},
    ]
    # Ensure the actual file path is templates/choose_login.html
    return render_template("choose_login.html", roles=roles)
