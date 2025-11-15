# -*- coding: utf-8 -*-
from __future__ import annotations
import importlib
import logging
from typing import Iterable
from flask import Flask, Blueprint

log = logging.getLogger(__name__)

# Curated list. Keep only modules that actually export a `bp`.
# NOTE: We temporarily remove "erp.api" to avoid noisy imports until it's ready.
BLUEPRINT_CANDIDATES: list[str] = [
    "erp.web",
    "erp.main",
    "erp.health",
    "erp.inventory",
    "erp.analytics",
    "erp.crm",
    # Optional submodules (only loaded if present and export `bp`)
    # "erp.api.v1",
    # "erp.bot.webhook",
    # "erp.webhook.incoming",
]

def _try_import(modname: str):
    try:
        return importlib.import_module(modname)
    except ModuleNotFoundError:
        return None
    except Exception as exc:
        log.warning("Import error in %s: %s", modname, exc)
        return None

def _maybe_register(app: Flask, modname: str) -> bool:
    mod = _try_import(modname)
    if not mod:
        return False

    bp = getattr(mod, "bp", None)
    if not isinstance(bp, Blueprint):
        log.debug("Module %s has no `bp`; skipped.", modname)
        return False

    # Skip if a blueprint with the same name is already registered
    if bp.name in app.blueprints:
        log.info("Blueprint %s already registered; skipping duplicate (%s)", bp.name, modname)
        return False

    app.register_blueprint(bp)
    log.info("Registered blueprint: %s (%s)", bp.name, modname)
    return True

def register_blueprints(app: Flask, extra: Iterable[str] | None = None) -> None:
    seen = set()
    for modname in BLUEPRINT_CANDIDATES + list(extra or []):
        if modname in seen:
            continue
        seen.add(modname)
        _maybe_register(app, modname)
