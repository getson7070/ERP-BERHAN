"""Simple plugin loader for the ERP system."""
import importlib
import pkgutil
from pathlib import Path
from typing import List

from .registry import register as registry_register, get_plugins


def load_plugins(app) -> List[str]:
    """Load plugins from the configured plugins directory."""
    plugin_path = Path(app.config.get('PLUGIN_PATH', 'plugins'))
    if not plugin_path.exists():
        return []
    loaded = []
    for mod in pkgutil.iter_modules([str(plugin_path)]):
        module = importlib.import_module(f"plugins.{mod.name}")
        if hasattr(module, 'register'):
            module.register(app, registry_register)
            loaded.append(mod.name)
    app.config['LOADED_PLUGINS'] = loaded
    app.config['PLUGIN_REGISTRY'] = get_plugins()
    return loaded
