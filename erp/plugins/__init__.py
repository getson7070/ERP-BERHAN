"""Simple plugin loader for the ERP system."""

import builtins
import importlib.util
import pkgutil
from pathlib import Path
from typing import List

from .registry import register as registry_register, get_plugins


def load_plugins(app) -> List[str]:
    """Load plugins from the configured plugins directory."""
    plugin_path = Path(app.config.get("PLUGIN_PATH", "plugins"))
    allowlist = set(app.config.get("PLUGIN_ALLOWLIST", []))
    sandbox_enabled = app.config.get("PLUGIN_SANDBOX_ENABLED", False)
    if not plugin_path.exists():
        return []
    loaded: List[str] = []
    for mod in pkgutil.iter_modules([str(plugin_path)]):
        if allowlist and mod.name not in allowlist:
            continue
        spec = importlib.util.spec_from_file_location(mod.name, plugin_path / f"{mod.name}.py")
        if not spec or not spec.loader:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "register"):
            try:
                if sandbox_enabled:
                    safe_builtins = {"__build_class__": builtins.__build_class__, "range": range, "len": len}
                    exec(
                        module.register.__code__,
                        {"app": app, "registry": registry_register, "__builtins__": safe_builtins},
                    )
                else:
                    module.register(app, registry_register)
                loaded.append(mod.name)
            except Exception:
                continue
    app.config["LOADED_PLUGINS"] = loaded
    app.config["PLUGIN_REGISTRY"] = get_plugins()
    return loaded
