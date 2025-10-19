from __future__ import annotations
from flask import Blueprint, Response
bp = Blueprint('projects', __name__, url_prefix='/projects')
@bp.get('/')
def index(): return Response('ok', mimetype='text/plain')
