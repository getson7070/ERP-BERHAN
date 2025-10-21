# ensure these metric names exist
try:
    from prometheus_client import Counter
    metrics = {
        "auth_failure": Counter("auth_failure_total", "Auth failures"),
        "auth_mfa_fail": Counter("auth_mfa_failure_total", "MFA failures"),
        "auth_lock": Counter("auth_lock_total", "Account lock events"),
        "telegram_send_fail": Counter("telegram_send_failure_total", "Telegram send failures"),
    }
except Exception:
    metrics = {}


