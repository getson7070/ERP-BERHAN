"""Module: forms.py — audit-added docstring. Refine with precise purpose when convenient."""
from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Email, Length, Optional

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Sign in")

class FeedbackForm(FlaskForm):
    name = StringField("Name", validators=[Optional(), Length(max=120)])
    message = StringField("Message", validators=[DataRequired(), Length(min=3, max=500)])
    submit = SubmitField("Send")

class ItemForm(FlaskForm):
    sku = StringField("SKU", validators=[DataRequired(), Length(max=64)])
    name = StringField("Name", validators=[DataRequired(), Length(max=255)])
    qty_on_hand = IntegerField("Qty On Hand", validators=[Optional()])
    price = DecimalField("Price", places=2, rounding=None, validators=[Optional()])
    submit = SubmitField("Save")



