# erp/utils/__init__.py
"""Utility helpers shared across ERP modules."""

from __future__ import annotations

from flask import Request, current_app, request, session


def resolve_org_id(default: int = 1, req: Request | None = None) -> int:
    """Determine the active organisation id for the current request.

    The upgraded blueprints accept an ``org_id`` query parameter, fall back to
    a value stored in the session, and finally to the provided default.  The
    helper is deliberately defensive—if parsing fails it logs a warning and
    returns the default instead of raising, keeping endpoints predictable.
    """

    req = req or request
    if req is not None:
        candidate = req.args.get("org_id") or req.headers.get("X-Org-Id")
        if candidate:
            try:
                return int(candidate)
            except (TypeError, ValueError):
                current_app.logger.warning("Invalid org_id %s; using default", candidate)
    try:
        stored = session.get("org_id")
        if stored is not None:
            return int(stored)
    except (TypeError, ValueError):
        current_app.logger.debug("Session org_id invalid; defaulting")
    return int(default)


__all__ = ["resolve_org_id"]


