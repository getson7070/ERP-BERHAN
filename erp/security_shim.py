import os

def _flag(env: str, default: bool = False) -> bool:
    v = os.getenv(env)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}

def compute_activation_for_device(device_id: str) -> dict:
    # Adjust defaults as you like via environment variables on Render
    return {
        "show_client":   _flag("ENABLE_CLIENT_LOGIN",   True),
        "show_employee": _flag("ENABLE_EMPLOYEE_LOGIN", False),  # Warehouse hidden by default
        "show_admin":    _flag("ENABLE_ADMIN_LOGIN",    False),
    }
