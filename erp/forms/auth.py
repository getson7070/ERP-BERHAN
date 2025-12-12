"""Authentication-related WTForms definitions."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    """Login form for HTML-based authentication.

    - CSRF is handled automatically by FlaskForm / Flask-WTF.
    - login_uuid is a hidden field used to correlate login attempts
      in audit logs or to tie a browser session to a UUID.
    """

    login_uuid = HiddenField("Login UUID")

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
            Length(max=255),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, max=128, message="Password must be at least 8 characters."),
        ],
    )

    remember_me = BooleanField("Remember me")

    submit = SubmitField("Sign in")
