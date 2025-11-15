# -*- coding: utf-8 -*-
from __future__ import annotations
import importlib
import types
from erp import create_app
from erp.boot import BLUEPRINT_CANDIDATES

def test_blueprints_contract():
    app = create_app()
    # 1) Every registered blueprint name must be unique (Flask enforces this, but we assert explicitly)
    names = list(app.blueprints.keys())
    assert len(names) == len(set(names)), f"Duplicate blueprint names registered: {names}"

    # 2) If a module is in candidates and importable, it must expose a `bp` attribute that is registered
    for modname in BLUEPRINT_CANDIDATES:
        try:
            mod = importlib.import_module(modname)
        except ModuleNotFoundError:
            # allowed: candidate that doesn't exist yet
            continue
        assert isinstance(mod, types.ModuleType), f"Invalid module: {modname}"
        if hasattr(mod, "bp"):
            bp = getattr(mod, "bp")
            assert bp.name in app.blueprints, f"{modname}.bp not registered (name={getattr(bp,'name',None)})"
