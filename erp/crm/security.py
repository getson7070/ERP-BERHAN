# -*- coding: utf-8 -*-
from __future__ import annotations
from flask import Blueprint

# Optional security routes; keep separate from main CRM routes.
bp = Blueprint("crm_security", __name__, url_prefix="/crm/security")

@bp.get("/health")
def health():
    return {"module": "crm.security", "ok": True}