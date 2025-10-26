# erp/middleware/lan_gate.py
import os, ipaddress
from flask import request, abort

def _cidrs():
    raw = os.getenv("ALLOWED_CIDRS","").split(",")
    out = []
    for x in raw:
        x = x.strip()
        if not x: continue
        try:
            out.append(ipaddress.ip_network(x, strict=False))
        except ValueError:
            pass
    return out

def within_allowed(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _cidrs())

def block_non_lan_for_sensitive_paths(app):
    @app.before_request
    def _gate():
        path = request.path or ""
        if path.startswith("/auth/login/admin") or path.startswith("/auth/login/employee"):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr) or ""
            if not within_allowed(ip):
                abort(403)
    return app
