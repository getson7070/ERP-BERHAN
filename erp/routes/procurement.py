"""Procurement UI endpoints for purchase orders and import tracking."""

from __future__ import annotations

from flask import Blueprint, render_template

from erp.security import require_roles

bp = Blueprint("procurement", __name__, url_prefix="/procurement")


@bp.get("/")
@require_roles("procurement", "inventory", "admin")
def index():
    return render_template("procurement/index.html", title="Procurement & Imports")


@bp.get("/new")
@require_roles("procurement", "inventory", "admin")
def add():
    return render_template("procurement/add.html", title="New Procurement Ticket")



