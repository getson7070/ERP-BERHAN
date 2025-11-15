"""Compatibility shim that proxies to the canonical inventory blueprint package."""
from __future__ import annotations

import sys
from types import ModuleType

from . import inventory as _inventory

_exports = tuple(getattr(_inventory, "__all__", ("bp", "create_item", "list_items", "get_item", "update_item", "delete_item", "get_jwt"))))
for _name in _exports:
    globals()[_name] = getattr(_inventory, _name)


class _ProxyModule(ModuleType):
    def __getattr__(self, name):
        return getattr(_inventory, name)

    def __setattr__(self, name, value):
        setattr(_inventory, name, value)
        super().__setattr__(name, value)


_proxy = _ProxyModule(__name__)
_proxy.__dict__.update(globals())
sys.modules[__name__] = _proxy

__all__ = _exports
