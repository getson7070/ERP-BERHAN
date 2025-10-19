# erp/middleware/idempotency.py
from __future__ import annotations

from functools import wraps
from flask import request, jsonify
from erp import db
from erp.models.idempotency import IdempotencyKey

def idempotent(endpoint_name: str, status_code_on_duplicate: int = 200):
    """
    Decorator that enforces exactly-once semantics per Idempotency-Key header.

    Clients must send:  Idempotency-Key: <opaque unique value>
    If the same key is seen again, we short-circuit with status_code_on_duplicate.
    """
    def wrap(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            key = request.headers.get("Idempotency-Key")
            if not key:
                return jsonify({"error": "Missing Idempotency-Key header"}), 409

            # Already used?
            exists = IdempotencyKey.query.filter_by(key=key).first()
            if exists:
                return jsonify({"status": "duplicate"}), status_code_on_duplicate

            db.session.add(IdempotencyKey(key=key, endpoint=endpoint_name))
            db.session.flush()  # reserve the key before executing handler

            try:
                resp = fn(*args, **kwargs)
                db.session.commit()
                return resp
            except Exception:
                # Roll back both the handler and the reserved key to allow retry.
                db.session.rollback()
                raise
        return inner
    return wrap


