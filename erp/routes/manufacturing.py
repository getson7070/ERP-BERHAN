"""Module: routes/manufacturing.py — audit-added docstring. Refine with precise purpose when convenient."""
from __future__ import annotations
from flask import Blueprint, Response
bp = Blueprint('manufacturing', __name__, url_prefix='/manufacturing')
@bp.get('/')
def index(): return Response('ok', mimetype='text/plain')



