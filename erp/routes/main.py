from flask import Blueprint, render_template, request, redirect, url_for, flash

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("choose_login.html")

@main_bp.route("/help")
def help_page():
    return render_template("help.html")

@main_bp.route("/privacy")
def privacy_page():
    privacy_config = {
        "company_name": "Berhan Pharma PLC",
        "officer_email": "info@berhanpharma.com",
        "last_update": "October 2025",
        "policy_summary": "We value your privacy and protect your data under Ethiopian and international data protection principles.",
    }
    return render_template("privacy.html", privacy_config=privacy_config)

@main_bp.route("/feedback", methods=["GET", "POST"])
def feedback_page():
    if request.method == "POST":
        msg = request.form.get("feedback")
        # In production: store to DB or email
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("main.feedback_page"))
    return render_template("feedback.html")
