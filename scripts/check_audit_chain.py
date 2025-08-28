#!/usr/bin/env python3
"""Audit log integrity check script."""
from erp.audit import check_audit_chain

if __name__ == "__main__":
    breaks = check_audit_chain()
    if breaks:
        print(f"Audit chain broken: {breaks} issues detected")
    else:
        print("Audit chain verified")
