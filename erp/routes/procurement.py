from __future__ import annotations
from flask import Blueprint, Response
bp = Blueprint('procurement', __name__, url_prefix='/procurement')
@bp.get('/')
def index(): return Response('ok', mimetype='text/plain')
