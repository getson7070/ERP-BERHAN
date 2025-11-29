"""Tenant context middleware that enforces org scoping per request."""
from __future__ import annotations

from flask import abort, current_app, g, request, session

from erp.public_paths import PUBLIC_PATHS, PUBLIC_PREFIXES

try:  # Flask-Login optional in some environments
    from flask_login import current_user
except Exception:  # pragma: no cover
    current_user = None  # type: ignore


def _candidate_from_user():
    if current_user is None:
        return None
    try:
        user = current_user
    except Exception:  # pragma: no cover
        return None
    if not getattr(user, "is_authenticated", False):
        return None
    for attr in ("org_id", "organization_id", "tenant_id"):
        value = getattr(user, attr, None)
        if value:
            return value
    # Some roles embed org context into session
    org_map = getattr(user, "organizations", None)
    if org_map:
        try:
            first = next(iter(org_map))
            return getattr(first, "id", None)
        except StopIteration:  # pragma: no cover
            return None
    return None


def _candidate_from_request():
    for key in ("org_id", "tenant_id"):
        if key in request.args:
            return request.args.get(key)
    headers = request.headers
    for key in ("X-Org-Id", "X-Tenant-Id"):
        if headers.get(key):
            return headers.get(key)
    return None


def _candidate_from_session():
    try:
        if "org_id" in session:
            return session["org_id"]
    except Exception:  # pragma: no cover
        return None
    return None


def _is_allowlisted_path(path: str) -> bool:
    """Paths that must never hard-fail for missing org context.

    Health/status endpoints must mirror ``erp.security_gate`` to keep load balancers
    and k8s probes working: /health, /healthz, /health/ready, /health/live,
    /health/readyz, /healthz/ready, /readyz, /status, /status/health, and
    /status/healthz. Auth and static assets remain reachable before a tenant is
    chosen.
    """

    if path in PUBLIC_PATHS or (path.endswith("/") and path[:-1] in PUBLIC_PATHS):
        return True

    extras = {
        "/",  # root redirect should be reachable
        "/register",
        "/favicon.ico",
    }
    if path in extras:
        return True

    return path.startswith(PUBLIC_PREFIXES)


def _normalize(value, default):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        current_app.logger.warning("Invalid org id %s; falling back", value)
        return default


def install_tenant_guard(app):
    """Populate ``g.org_id`` early in the request lifecycle."""

    @app.before_request
    def _bind_org_context():
        path = request.path or "/"
        allowlisted = _is_allowlisted_path(path)
        candidate = (
            _candidate_from_request()
            or _candidate_from_session()
            or _candidate_from_user()
        )
        fallback = app.config.get("DEFAULT_ORG_ID", 1)
        org_id = _normalize(candidate, fallback)
        strict = app.config.get("STRICT_ORG_BOUNDARIES", True)
        testing = app.config.get("TESTING")
        if org_id is None:
            if (
                not strict
                or testing
                or allowlisted
                or app.config.get("ALLOW_INSECURE_DEFAULTS") == "1"
            ):
                org_id = fallback
            else:
                abort(400, description="org_id_required")
        g.org_id = int(org_id)
        session.setdefault("org_id", int(org_id))
