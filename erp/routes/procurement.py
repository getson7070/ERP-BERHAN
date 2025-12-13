"""Procurement UI endpoints for purchase orders and import tracking."""

from __future__ import annotations

from flask import Blueprint, render_template

from erp.security_decorators_phase2 import require_permission

bp = Blueprint("procurement", __name__, url_prefix="/procurement")


@bp.get("/")
@require_permission("procurement", "view")
def index():
    return render_template("procurement/index.html", title="Procurement & Imports")


@bp.get("/new")
@require_permission("procurement", "create")
def add():
    return render_template("procurement/add.html", title="New Procurement Ticket")
