# erp/security_shim.py
# Minimal no-op shims so imports never break during Alembic runs.

def read_device_id(request=None) -> str | None:
    return None

def compute_activation_for_device(device_id: str | None):
    # return a structure compatible with your templates, keep everything enabled by default
    return {"show_client": True, "show_employee": True, "show_admin": True}
