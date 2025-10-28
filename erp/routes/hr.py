"""Module: routes/hr.py — audit-added docstring. Refine with precise purpose when convenient."""
from __future__ import annotations
from flask import Blueprint, Response
bp = Blueprint('hr', __name__, url_prefix='/hr')
@bp.get('/')
def index(): return Response('ok', mimetype='text/plain')



