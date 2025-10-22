
import uuid
from flask import g, request

HEADER = "X-Request-ID"

def ensure_request_id():
    rid = request.headers.get(HEADER) or str(uuid.uuid4())
    g.request_id = rid

def add_request_id_to_response(response):
    rid = getattr(g, "request_id", None)
    if rid:
        response.headers.setdefault(HEADER, rid)
    return response
