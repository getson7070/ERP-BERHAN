from __future__ import annotations
from flask import Blueprint, Response
bp = Blueprint('crm', __name__, url_prefix='/crm')
@bp.get('/')
def index(): return Response('ok', mimetype='text/plain')


