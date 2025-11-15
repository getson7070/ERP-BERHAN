"""Plugin discovery helpers used by the blueprint tests."""

from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Dict


def _allowed() -> set[str]:
    raw = os.getenv("ERP_ALLOWED_PLUGINS", "")
    return {p.strip() for p in raw.split(",") if p.strip()}


def load_entrypoint(dotted: str):
    allowed = _allowed()
    if allowed and dotted not in allowed:
        raise ValueError(f"Plugin '{dotted}' not in allow-list")
    if ":" not in dotted:
        raise ValueError("Use 'module.submodule:attribute' format")
    module, attr = dotted.rsplit(":", 1)
    mod = importlib.import_module(module)
    return getattr(mod, attr)


def _iter_plugin_modules(base_path: Path) -> Dict[str, ModuleType]:
    modules: Dict[str, ModuleType] = {}
    for file in sorted(base_path.glob("*.py")):
        if file.name.startswith("_"):
            continue
        module_name = f"plugins.{file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception:
                continue
            modules[module_name] = module
    return modules


def load_plugins(app) -> dict[str, Any]:
    """Load plugin modules from the configured path.

    Each plugin exposes a ``register(app, registry)`` function where the
    second argument is a callback receiving ``(name, payload)``.  The
    registry callback honours both the application allow-list and the
    environment variable based allow-list so tests can simulate different
    policies without hitting the filesystem.
    """

    plugin_path = Path(app.config.get("PLUGIN_PATH", "plugins")).resolve()
    allowlist = {name.lower() for name in app.config.get("PLUGIN_ALLOWLIST", [])}
    env_allow = {name.lower() for name in _allowed()}

    registry: dict[str, Any] = {}

    def _register(name: str, payload: Any) -> None:
        key = name.lower()
        if allowlist and key not in allowlist:
            return
        if env_allow and key not in env_allow:
            return
        registry[name] = payload

    if not plugin_path.exists() or not plugin_path.is_dir():
        return registry

    modules = _iter_plugin_modules(plugin_path)

    for module in modules.values():
        register_fn = getattr(module, "register", None)
        if callable(register_fn):
            try:
                register_fn(app, _register)
            except Exception:
                continue

    return registry


__all__ = ["load_entrypoint", "load_plugins"]
