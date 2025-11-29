import importlib, pkgutil, os
from flask import Blueprint

def register_all(app):
pkg = 'erp'
count = 0
for finder, name, ispkg in pkgutil.walk_packages([pkg]):
modname = f"{pkg}.{name}"
try:
m = importlib.import_module(modname)
except Exception:
continue
cand = []
for attr in ('bp','blueprint','Blueprint','api','router'):
if hasattr(m, attr):
obj = getattr(m, attr)
if isinstance(obj, Blueprint):
cand.append(obj)
for b in cand:
try:
app.register_blueprint(b)
count += 1
except Exception:
pass
return count

