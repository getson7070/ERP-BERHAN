# erp/forms.py
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
    """Basic email/password login form with CSRF protection."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Invalid email format."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must be at least 8 characters."),
        ],
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class ForgotPasswordForm(FlaskForm):
    """Request a password reset link."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Invalid email address."),
        ],
    )
    submit = SubmitField("Send Reset Link")


class ChangePasswordForm(FlaskForm):
    """Change password for an authenticated user."""

    old_password = PasswordField(
        "Old Password",
        validators=[DataRequired(message="Old password is required.")],
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="New password is required."),
            Length(min=8, message="Password must be at least 8 characters."),
            EqualTo("confirm_password", message="Passwords must match."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(message="Please confirm the new password.")],
    )
    submit = SubmitField("Change Password")


class ItemForm(FlaskForm):
    """
    Simple item creation form used by erp.routes.inventory.new_item.

    NOTE:
    - Serial numbers (for devices/equipment) and lot/batch numbers (for reagents)
      are handled in the inventory models (InventorySerial, Lot, etc.).
    - This form is only for the base catalog item; stock & serial/lot flows
      can be layered on top with dedicated forms/views.
    """

    sku = StringField(
        "SKU",
        validators=[
            DataRequired(message="SKU is required."),
            Length(max=64, message="SKU must be at most 64 characters."),
        ],
    )
    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Item name is required."),
            Length(max=255, message="Name must be at most 255 characters."),
        ],
    )

    # These map directly to how new_item() in erp.routes.inventory uses the form:
    #   qty_on_hand=form.qty_on_hand.data or 0
    #   price=form.price.data or 0
    qty_on_hand = IntegerField(
        "Quantity on Hand",
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0, message="Quantity cannot be negative."),
        ],
    )
    price = DecimalField(
        "Unit Price",
        default=Decimal("0.00"),
        places=2,
        rounding=None,
        validators=[
            Optional(),
            NumberRange(min=0, message="Price cannot be negative."),
        ],
    )

    submit = SubmitField("Save Item")


class TicketForm(FlaskForm):
    """Example non-auth form kept for future use / demos."""

    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=100, message="Title must be at most 100 characters."),
        ],
    )
    description = TextAreaField(
        "Description",
        validators=[
            DataRequired(message="Description is required."),
            Length(max=500, message="Description must be at most 500 characters."),
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
    submit = SubmitField("Create Ticket")
