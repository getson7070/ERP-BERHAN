"""
Safe plugin loader (replaces any exec()/eval() usage).
Allow-list based; configure allowed entrypoints via env ERP_ALLOWED_PLUGINS (comma-separated).
Example values: "erp.plugins.foo:Plugin,erp.plugins.bar:init"
"""
import os
import importlib

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
