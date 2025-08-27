#!/usr/bin/env python3
"""Validate that all blueprints import correctly."""
import importlib
import pkgutil
import sys
from flask import Flask
from erp.app import _blueprints_from

PACKAGES = ["erp.routes", "erp.blueprints", "plugins"]

def main() -> int:
    app = Flask(__name__)
    count = 0
    for pkg_name in PACKAGES:
        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            continue
        for bp in _blueprints_from(pkg):
            app.register_blueprint(bp)
            count += 1
    print(f"registered {count} blueprints")
    return 0

if __name__ == "__main__":
    sys.exit(main())
