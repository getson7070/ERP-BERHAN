from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
    jsonify,
)
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    DateField,
    FloatField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired, Length, NumberRange
from datetime import datetime, timedelta
import pyotp
import json
import secrets
from typing import cast
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    decode_token,
)

from db import get_db, redis_client
from erp.utils import (
    hash_password,
    verify_password,
    login_required,
    has_permission,
    roles_required,
)
from erp.audit import log_audit
from erp import oauth, limiter

bp = Blueprint("auth", __name__)


def _check_backoff(email: str) -> tuple[str, int]:
    if redis_client.exists(f"lock:{email}"):
        lock_ttl = cast(int, redis_client.ttl(f"lock:{email}") or 0)
        return "locked", max(lock_ttl, 0)
    backoff_ttl = cast(int, redis_client.ttl(f"backoff:{email}") or 0)
    if backoff_ttl > 0:
        return "backoff", backoff_ttl
    return "ok", 0


def _record_failure(email: str, user) -> None:
    attempts = cast(int, redis_client.incr(f"fail:{email}") or 0)
    redis_client.expire(f"fail:{email}", current_app.config.get("LOCK_WINDOW", 300))
    if attempts > 1:
        delay = min(2 ** (attempts - 1), current_app.config.get("MAX_BACKOFF", 60))
        redis_client.setex(f"backoff:{email}", delay, 1)
    if attempts >= current_app.config.get("LOCK_THRESHOLD", 5):
        redis_client.setex(
            f"lock:{email}",
            current_app.config.get("ACCOUNT_LOCK_SECONDS", 900),
            1,
        )
        if user:
            user_id = user["id"] if isinstance(user, dict) else user["id"]
            org_id = user.get("org_id") if isinstance(user, dict) else user["org_id"]
            log_audit(
                user_id,
                org_id,
                "account_lock",
                f"failed_logins={attempts}",
            )


def _clear_failures(email: str, user) -> None:
    fail_count = redis_client.get(f"fail:{email}")
    was_locked = redis_client.delete(f"lock:{email}")
    redis_client.delete(f"fail:{email}")
    redis_client.delete(f"backoff:{email}")
    if user and (
        was_locked
        or (
            fail_count
            and int(cast(int, fail_count))
            >= current_app.config.get("LOCK_THRESHOLD", 5)
        )
    ):
        user_id = user["id"] if isinstance(user, dict) else user["id"]
        org_id = user.get("org_id") if isinstance(user, dict) else user["org_id"]
        log_audit(user_id, org_id, "account_unlock", "")


@bp.route("/auth/token", methods=["POST"])
@limiter.limit("2 per minute")
def issue_token():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    totp_code = data.get("totp")
    status, ttl = _check_backoff(email)
    if status == "locked":
        return {"error": "account_locked", "retry_after": ttl}, 403
    if status == "backoff":
        return {"error": "retry_later", "retry_after": ttl}, 429
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    user = dict(row) if row is not None else None
    if not user or not verify_password(password, user["password_hash"]):
        conn.close()
        _record_failure(email, user)
        return {"error": "invalid_credentials"}, 401
    if user["role"] in ("Admin", "Management"):
        if not user["mfa_secret"] or not pyotp.TOTP(
            user["mfa_secret"], issuer=current_app.config["MFA_ISSUER"]
        ).verify(totp_code or ""):
            conn.close()
            return {"error": "mfa_required"}, 401
    additional_claims = {"org_id": user.get("org_id")}
    access = create_access_token(
        identity=email,
        additional_claims=additional_claims,
        additional_headers={"kid": current_app.config.get("JWT_SECRET_ID", "v1")},  # type: ignore[call-arg]
    )
    refresh = create_refresh_token(
        identity=email,
        additional_claims=additional_claims,
        additional_headers={"kid": current_app.config.get("JWT_SECRET_ID", "v1")},  # type: ignore[call-arg]
    )
    refresh_jti = decode_token(refresh)["jti"]
    redis_client.setex(
        f"refresh:{refresh_jti}",
        timedelta(days=7),
        json.dumps({"email": email, "org_id": user.get("org_id")}),
    )
    current_app.logger.info("issued tokens for %s", email)
    conn.close()
    _clear_failures(email, user)
    return {"access_token": access, "refresh_token": refresh}


@bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    jti = get_jwt()["jti"]
    key = f"refresh:{jti}"
    stored = redis_client.get(key)
    if not stored:
        return {"error": "invalid_token"}, 401
    redis_client.delete(key)
    identity = get_jwt_identity()
    org_id = get_jwt().get("org_id")
    additional_claims = {"org_id": org_id}
    access = create_access_token(
        identity=identity,
        additional_claims=additional_claims,
        additional_headers={"kid": current_app.config.get("JWT_SECRET_ID", "v1")},  # type: ignore[call-arg]
    )
    refresh = create_refresh_token(
        identity=identity,
        additional_claims=additional_claims,
        additional_headers={"kid": current_app.config.get("JWT_SECRET_ID", "v1")},  # type: ignore[call-arg]
    )
    new_jti = decode_token(refresh)["jti"]
    redis_client.setex(
        f"refresh:{new_jti}",
        timedelta(days=7),
        json.dumps({"email": identity, "org_id": org_id}),
    )
    current_app.logger.info("refreshed token for %s", identity)
    return {"access_token": access, "refresh_token": refresh}


@bp.post("/auth/socket-token")
@login_required
def socket_token():
    """Issue a short-lived token for WebSocket authentication."""
    user_id = session.get("user_id")
    org_id = session.get("org_id")
    old = redis_client.get(f"socket_user:{user_id}")
    if old:
        redis_client.delete(f"socket_token:{old.decode()}")
    token = secrets.token_urlsafe(16)
    redis_client.setex(f"socket_token:{token}", 60, org_id)
    redis_client.setex(f"socket_user:{user_id}", 60, token)
    return jsonify({"token": token})


@bp.route("/choose_login", methods=["GET", "POST"])
def choose_login():
    class ChooseLoginForm(FlaskForm):
        login_type = SelectField(
            "Login Type",
            choices=[("employee", "Employee"), ("client", "Client")],
            validators=[DataRequired()],
        )
        submit = SubmitField("Continue")

    form = ChooseLoginForm()
    if form.validate_on_submit():
        login_type = form.login_type.data
        if login_type == "employee":
            return redirect(url_for("auth.employee_login"))
        elif login_type == "client":
            return redirect(url_for("auth.client_login"))
    return render_template("choose_login.html", form=form)


@bp.route("/oauth_login")
def oauth_login():
    redirect_uri = url_for("auth.oauth_callback", _external=True)
    return oauth.sso.authorize_redirect(redirect_uri)


@bp.route("/oauth_callback")
def oauth_callback():
    token = oauth.sso.authorize_access_token()
    resp = oauth.sso.get(current_app.config["OAUTH_USERINFO_URL"], token=token)
    profile = resp.json()
    email = profile.get("email")
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        conn.close()
        flash("Unauthorized user")
        return redirect(url_for("auth.choose_login"))
    session.permanent = True
    session["logged_in"] = True
    session["role"] = user["role"] or "Employee"
    session["username"] = email
    session["permissions"] = (
        user["permissions"].split(",") if user["permissions"] else []
    )
    session["org_id"] = user.get("org_id")
    log_audit(user["id"], user.get("org_id"), "login", "SSO")
    conn.execute(
        "UPDATE users SET last_login = ? WHERE email = ?",
        (datetime.now(), email),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("main.dashboard"))


@bp.route("/employee_login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def employee_login():
    class LoginForm(FlaskForm):
        email = StringField("Email", validators=[DataRequired()])
        password = PasswordField("Password", validators=[DataRequired()])
        totp = StringField(
            "MFA Code", validators=[DataRequired(), Length(min=6, max=6)]
        )
        submit = SubmitField("Login")

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        status, ttl = _check_backoff(email)
        if status == "locked":
            flash("Account temporarily locked. Try again later.")
            return render_template("employee_login.html", form=form)
        if status == "backoff":
            flash(f"Too many attempts. Retry after {ttl} seconds.")
            return render_template("employee_login.html", form=form)
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND user_type = ? AND approved_by_ceo = TRUE",
            (email, "employee"),
        ).fetchone()
        if (
            user
            and not user["account_locked"]
            and verify_password(password, user["password_hash"])
        ):
            if not user["mfa_secret"]:
                flash("MFA not configured for this account.")
            elif pyotp.TOTP(
                user["mfa_secret"], issuer=current_app.config["MFA_ISSUER"]
            ).verify(form.totp.data):
                session.permanent = True
                session["logged_in"] = True
                session["role"] = user["role"] or "Employee"
                session["username"] = email
                session["org_id"] = user.get("org_id")
                session["permissions"] = (
                    user["permissions"].split(",") if user["permissions"] else []
                )
                session["mfa_verified"] = True
                conn.execute(
                    "UPDATE users SET last_login = ?, failed_attempts = 0 WHERE email = ?",
                    (datetime.now(), email),
                )
                log_audit(user["id"], user.get("org_id"), "login", "employee password")
                conn.commit()
                conn.close()
                _clear_failures(email, user)
                return redirect(url_for("main.dashboard"))
            else:
                flash("Invalid MFA code.")
        else:
            if user:
                if user["account_locked"]:
                    flash("Account locked due to too many failed attempts.")
                else:
                    conn.execute(
                        "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE email = ?",
                        (email,),
                    )
                    conn.commit()
                    _record_failure(email, user)
                    flash("Invalid email/password or not approved.")
            else:
                flash("Invalid email/password or not approved.")
            conn.close()
    return render_template("employee_login.html", form=form)


@bp.route("/client_login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def client_login():
    class LoginForm(FlaskForm):
        email = StringField("Email", validators=[DataRequired()])
        password = PasswordField("Password", validators=[DataRequired()])
        totp = StringField(
            "MFA Code", validators=[DataRequired(), Length(min=6, max=6)]
        )
        submit = SubmitField("Login")

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        status, ttl = _check_backoff(email)
        if status == "locked":
            flash("Account temporarily locked. Try again later.")
            return render_template("client_login.html", form=form)
        if status == "backoff":
            flash(f"Too many attempts. Retry after {ttl} seconds.")
            return render_template("client_login.html", form=form)
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND user_type = ? AND approved_by_ceo = TRUE",
            (email, "client"),
        ).fetchone()
        if (
            user
            and not user["account_locked"]
            and verify_password(password, user["password_hash"])
        ):
            if not user["mfa_secret"]:
                flash("MFA not configured for this account.")
            elif pyotp.TOTP(
                user["mfa_secret"], issuer=current_app.config["MFA_ISSUER"]
            ).verify(form.totp.data):
                session.permanent = True
                session["logged_in"] = True
                session["role"] = "Client"
                session["tin"] = user["tin"]
                session["username"] = email
                session["org_id"] = user.get("org_id")
                session["permissions"] = (
                    user["permissions"].split(",") if user["permissions"] else []
                )
                session["mfa_verified"] = True
                conn.execute(
                    "UPDATE users SET last_login = ?, failed_attempts = 0 WHERE email = ?",
                    (datetime.now(), email),
                )
                log_audit(user["id"], user.get("org_id"), "login", "client password")
                conn.commit()
                conn.close()
                _clear_failures(email, user)
                return redirect(url_for("main.dashboard"))
            else:
                flash("Invalid MFA code.")
        else:
            if user:
                if user["account_locked"]:
                    flash("Account locked due to too many failed attempts.")
                else:
                    conn.execute(
                        "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE email = ?",
                        (email,),
                    )
                    conn.commit()
                    _record_failure(email, user)
                    flash("Invalid email/password or not approved.")
            else:
                flash("Invalid email/password or not approved.")
            conn.close()
    return render_template("client_login.html", form=form)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.choose_login"))


@bp.route("/client_registration", methods=["GET", "POST"])
def client_registration():
    class ClientRegistrationForm(FlaskForm):
        tin = StringField("TIN", validators=[DataRequired(), Length(min=10, max=10)])
        institution_name = StringField("Institution Name", validators=[DataRequired()])
        address = StringField("Address", validators=[DataRequired()])
        phone = StringField(
            "Phone", validators=[DataRequired(), Length(min=10, max=10)]
        )
        region = SelectField("Region", validators=[DataRequired()])
        city = SelectField("City", validators=[DataRequired()])
        email = StringField("Email", validators=[DataRequired()])
        password = PasswordField("Password", validators=[DataRequired()])
        submit = SubmitField("Register")

    conn = get_db()
    form = ClientRegistrationForm()
    form.region.choices = [
        (r["region"], r["region"])
        for r in conn.execute("SELECT DISTINCT region FROM regions_cities").fetchall()
    ]
    if not form.region.data and form.region.choices:
        form.region.data = form.region.choices[0][0]
    form.city.choices = (
        [
            (c["city"], c["city"])
            for c in conn.execute(
                "SELECT city FROM regions_cities WHERE region = ?", (form.region.data,)
            ).fetchall()
        ]
        if form.region.data
        else []
    )
    if form.validate_on_submit():
        tin = form.tin.data
        if not tin.isdigit():
            flash("TIN must be a 10-digit number.")
            conn.close()
            return render_template("client_registration.html", form=form)
        institution_name = form.institution_name.data
        address = form.address.data
        phone = form.phone.data
        if not (phone.startswith(("09", "07")) and phone.isdigit()):
            flash("Phone must be a 10-digit number starting with 09 or 07.")
            conn.close()
            return render_template("client_registration.html", form=form)
        region = form.region.data
        city = form.city.data
        email = form.email.data
        password = form.password.data
        if conn.execute(
            "SELECT * FROM users WHERE tin = ? OR email = ?", (tin, email)
        ).fetchone():
            flash("TIN or email already registered.")
            conn.close()
            return render_template("client_registration.html", form=form)
        password_hash = hash_password(password)
        mfa_secret = pyotp.random_base32()
        conn.execute(
            """
            INSERT INTO users (user_type, tin, institution_name, address, phone, region, city, email, password_hash, mfa_secret, permissions, approved_by_ceo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "client",
                tin,
                institution_name,
                address,
                phone,
                region,
                city,
                email,
                password_hash,
                mfa_secret,
                "put_order,my_orders,order_status,maintenance_request,maintenance_status,message",
                False,
            ),
        )
        conn.commit()
        flash(f"Set up your authenticator with this secret: {mfa_secret}", "info")
        conn.close()
        return redirect(url_for("auth.choose_login"))
    conn.close()
    return render_template("client_registration.html", form=form)


@bp.route("/employee_registration", methods=["GET", "POST"])
@login_required
@roles_required("Management")
def employee_registration():
    if not has_permission("user_management"):
        return redirect(url_for("main.dashboard"))

    class EmployeeRegistrationForm(FlaskForm):
        username = StringField(
            "Username (Phone Number)",
            validators=[DataRequired(), Length(min=10, max=10)],
        )
        email = StringField("Email", validators=[DataRequired()])
        password = PasswordField("Password", validators=[DataRequired()])
        role = SelectField(
            "Role",
            choices=[
                ("Sales Rep", "Sales Rep"),
                ("Storekeeper", "Storekeeper"),
                ("Accountant", "Accountant"),
                ("Management", "Management"),
                ("Cashier", "Cashier"),
                ("Tender", "Tender"),
            ],
            validators=[DataRequired()],
        )
        permissions = SelectMultipleField("Permissions", validators=[DataRequired()])
        hire_date = DateField("Hire Date", validators=[DataRequired()])
        salary = FloatField(
            "Salary (ETB)", validators=[DataRequired(), NumberRange(min=0)]
        )
        submit = SubmitField("Register")

    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        permissions = form.permissions.data
        hire_date = form.hire_date.data
        salary = form.salary.data
        conn = get_db()
        if conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?", (username, email)
        ).fetchone():
            flash("Username or email already registered.")
            conn.close()
            return render_template("employee_registration.html", form=form)
        password_hash = hash_password(password)
        mfa_secret = pyotp.random_base32()
        conn.execute(
            """
            INSERT INTO users (user_type, username, email, password_hash, mfa_secret, permissions, approved_by_ceo, hire_date, salary, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "employee",
                username,
                email,
                password_hash,
                mfa_secret,
                permissions,
                False,
                hire_date,
                salary,
                role,
            ),
        )
        conn.commit()
        flash(f"Set up your authenticator with this secret: {mfa_secret}", "info")
        conn.close()
        return redirect(url_for("main.dashboard"))
    return render_template("employee_registration.html", form=form)
