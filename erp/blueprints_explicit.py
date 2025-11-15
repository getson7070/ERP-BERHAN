# -*- coding: utf-8 -*-
"""
Curated allowlist of blueprints to register with (module_path, url_prefix).
Only modules listed here will be attempted, in order.
"""
ALLOWLIST = [
    ("erp.web", "/"),
    ("erp.inventory", "/inventory"),
    ("erp.crm", "/crm"),
    ("erp.analytics", "/analytics"),
    ("erp.auth.mfa_routes", "/auth"),
    ("erp.views.main", "/"),
    # Add more when ready:
    # ("erp.procurement", "/procurement"),
]
