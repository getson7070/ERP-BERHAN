import bleach
from flask import request, g

_ALLOWED_TAGS = []
_ALLOWED_ATTRIBUTES = {}
_STR_TYPES = (str,)

def _sanitize_value(v):
    if isinstance(v, _STR_TYPES):
        return bleach.clean(v, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES, strip=True)
    return v

def _sanitize_mapping(m):
    clean = {}
    for k, v in m.items():
        if isinstance(v, dict):
            clean[k] = _sanitize_mapping(v)
        elif isinstance(v, list):
            clean[k] = [_sanitize_value(i) for i in v]
        else:
            clean[k] = _sanitize_value(v)
    return clean

def sanitize_request_payload():
    try:
        if request.is_json:
            g.sanitized_json = _sanitize_mapping(request.get_json(silent=True) or {})
        else:
            g.sanitized_form = {k: _sanitize_value(v) for k, v in request.form.items()}
    except Exception:
        pass
