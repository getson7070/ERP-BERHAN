import os

REQUIRED = ("SECRET_KEY", "DATABASE_URL", "JWT_SECRET_KEY")

def validate(strict: bool) -> None:
    if not strict:
        return
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required envs for production: {', '.join(missing)}")
