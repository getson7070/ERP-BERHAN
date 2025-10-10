--- a/erp/routes/auth.py
+++ b/erp/routes/auth.py
@@
 from flask import Blueprint, render_template, request, redirect, url_for, flash, session
-from flask_login import login_user, logout_user, current_user, login_required
+from flask_login import login_user, logout_user, current_user, login_required
+from werkzeug.exceptions import TooManyRequests
+from datetime import datetime
+from erp.observability_ext import metrics  # optional counters
+from erp.extensions import limiter  # new: Flask-Limiter instance
 from erp.models import db, User

 auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

+@auth_bp.before_app_request
+def apply_security_headers():
+    # Basic hardening; Talisman could also be used
+    hs = {
+        "X-Content-Type-Options": "nosniff",
+        "X-Frame-Options": "DENY",
+        "Referrer-Policy": "no-referrer",
+        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
+    }
+    # set on response in after_request via app factory ideally
+    pass

-@auth_bp.route("/login", methods=["GET", "POST"])
+@auth_bp.route("/login", methods=["GET", "POST"])
+@limiter.limit("10/minute")  # rate-limit to blunt brute force
 def login():
     if request.method == "GET":
         if current_user.is_authenticated:
             return redirect(url_for("main.index"))
         return render_template("auth/login.html")
@@
-    email = request.form.get("email","").strip().lower()
-    password = request.form.get("password","")
+    email = request.form.get("email", "").strip().lower()
+    password = request.form.get("password", "")
+    token = request.form.get("token", "").strip()
+    remember = bool(request.form.get("remember"))
     user = User.query.filter_by(email=email).first()

-    if not user or not user.check_password(password):
-        flash("Invalid credentials", "error")
-        return render_template("auth/login.html"), 401
+    if not user:
+        flash("Invalid credentials", "error"); 
+        metrics["auth_failure"].inc() if metrics and "auth_failure" in metrics else None
+        return render_template("auth/login.html"), 401
+
+    if user.is_locked():
+        flash("Account temporarily locked due to failed attempts. Try again later.", "error")
+        metrics["auth_lock"].inc() if metrics and "auth_lock" in metrics else None
+        return render_template("auth/login.html"), 423
+
+    if not user.check_password(password):
+        user.register_failed_login(); db.session.commit()
+        flash("Invalid credentials", "error")
+        metrics["auth_failure"].inc() if metrics and "auth_failure" in metrics else None
+        return render_template("auth/login.html"), 401
+
+    # MFA
+    if user.mfa_enabled:
+        if not token or not user.verify_mfa_token(token):
+            flash("MFA token invalid. Use recovery code if needed.", "error")
+            metrics["auth_mfa_fail"].inc() if metrics and "auth_mfa_fail" in metrics else None
+            return render_template("auth/login.html"), 401
+
+    user.reset_failed_logins(); db.session.commit()
-    login_user(user)
+    login_user(user, remember=remember)
     return redirect(url_for("main.index"))
