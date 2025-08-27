"""Blueprint discovery and application security helpers.

The application dynamically locates and registers blueprints exposed as a
module level ``bp`` variable.  It also initialises authentication helpers such
as Flask-Security for role based access control and ``flask_jwt_extended`` for
API tokens.

See ``docs/blueprints.md`` for a high level overview of the discovery strategy.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
from types import ModuleType
from typing import Iterable

import pyotp
from flask import Blueprint, current_app
from flask_security import Security, SQLAlchemyUserDatastore
from flask_jwt_extended import JWTManager, create_access_token

from .extensions import db
from .models import User, Role

security = Security()
jwt = JWTManager()


def init_security(app):
    """Configure Flask-Security and JWT extensions."""

    app.config.setdefault("SECURITY_PASSWORD_SALT", os.environ.get("SECURITY_PASSWORD_SALT", "changeme"))
    app.config.setdefault("SECURITY_TWO_FACTOR_ENABLED_METHODS", ["authenticator"])
    app.config.setdefault("SECURITY_TOTP_ISSUER", app.config.get("MFA_ISSUER", "ERP-BERHAN"))
    app.config.setdefault("JWT_SECRET_KEY", app.config.get("JWT_SECRET"))
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore=user_datastore)
    jwt.init_app(app)
    return user_datastore


def generate_totp_uri(user: User) -> str:
    """Return provisioning URI for authenticator applications."""

    totp = pyotp.TOTP(user.mfa_secret, issuer=current_app.config.get("MFA_ISSUER", "ERP-BERHAN"))
    return totp.provisioning_uri(name=user.email)


def issue_api_token(identity: str) -> str:
    """Create a JWT for *identity*."""

    return create_access_token(identity=identity)


def _blueprints_from(pkg: ModuleType) -> Iterable[Blueprint]:
    """Yield blueprints defined in *pkg* and its descendants.

    Only attributes named ``bp`` that are actual :class:`~flask.Blueprint`
    instances are considered.  Import errors are ignored to avoid breaking
    the application if optional dependencies are missing.
    """

    bp = getattr(pkg, "bp", None)
    if isinstance(bp, Blueprint):
        yield bp

    prefix = pkg.__name__ + "."
    for _, modname, _ in pkgutil.walk_packages(pkg.__path__, prefix):
        try:
            module = importlib.import_module(modname)
        except Exception:  # pragma: no cover - best effort discovery
            continue
        bp = getattr(module, "bp", None)
        if isinstance(bp, Blueprint):
            yield bp


def register_blueprints(app) -> None:
    """Auto-discover and register blueprints.

    Packages under ``erp.routes``, ``erp.blueprints`` and ``plugins`` are
    scanned for modules exposing a top-level ``bp`` blueprint.  This makes it
    trivial to drop in new functionality without modifying the core
    application.
    """

    for package_name in ("erp.routes", "erp.blueprints", "plugins"):
        try:
            pkg = importlib.import_module(package_name)
        except ModuleNotFoundError:
            continue
        for bp in _blueprints_from(pkg):
            if bp.name not in app.blueprints:
                app.register_blueprint(bp)
