from __future__ import annotations

from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    SelectField,
    IntegerField,
    DecimalField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    Optional,
    NumberRange,
)


class LoginForm(FlaskForm):
    """Standard email/password login form with CSRF."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must be at least 8 characters."),
        ],
    )

    remember_me = BooleanField("Remember me")

    submit = SubmitField("Sign in")


class ForgotPasswordForm(FlaskForm):
    """Request a password reset link."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
        ],
    )

    submit = SubmitField("Send reset link")


class ChangePasswordForm(FlaskForm):
    """Change password for an authenticated user."""

    old_password = PasswordField(
        "Current password",
        validators=[DataRequired(message="Current password is required.")],
    )

    new_password = PasswordField(
        "New password",
        validators=[
            DataRequired(message="New password is required."),
            Length(min=8, message="Password must be at least 8 characters."),
            EqualTo("confirm_password", message="New passwords must match."),
        ],
    )

    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(message="Please confirm the new password.")],
    )

    submit = SubmitField("Change password")


class ItemForm(FlaskForm):
    """
    Base catalog item form used by inventory views.

    Serial numbers for devices/equipment and lot/batch numbers for reagents
    are handled in the inventory models and related flows; this form covers
    the master catalog item record (SKU, name, initial quantity, price).
    """

    sku = StringField(
        "SKU",
        validators=[
            DataRequired(message="SKU is required."),
            Length(max=64, message="SKU can be at most 64 characters."),
        ],
    )

    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Item name is required."),
            Length(max=255, message="Name can be at most 255 characters."),
        ],
    )

    # These map to how new_item() in erp.routes.inventory uses the form:
    #   qty_on_hand=form.qty_on_hand.data or 0
    #   price=form.price.data or 0
    qty_on_hand = IntegerField(
        "Quantity on hand",
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0, message="Quantity cannot be negative."),
        ],
    )

    price = DecimalField(
        "Unit price",
        default=Decimal("0.00"),
        places=2,
        rounding=None,
        validators=[
            Optional(),
            NumberRange(min=0, message="Price cannot be negative."),
        ],
    )

    submit = SubmitField("Save item")


class TicketForm(FlaskForm):
    """Generic ticket form kept for support/demo flows."""

    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=100, message="Title can be at most 100 characters."),
        ],
    )

    description = TextAreaField(
        "Description",
        validators=[
            DataRequired(message="Description is required."),
            Length(
                max=500,
                message="Description can be at most 500 characters.",
            ),
        ],
    )

    priority = SelectField(
        "Priority",
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        validators=[DataRequired(message="Priority is required.")],
    )

    submit = SubmitField("Create ticket")


__all__ = [
    "LoginForm",
    "ForgotPasswordForm",
    "ChangePasswordForm",
    "ItemForm",
    "TicketForm",
]
