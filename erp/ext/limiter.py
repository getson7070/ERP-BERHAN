from __future__ import annotations

import os
from typing import List

def _parse_limits(raw: str) -> List[str]:
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    return parts or ["200 per minute"]

def install_limiter(app):
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
    except Exception as e:  # pragma: no cover
        raise RuntimeError("flask-limiter not installed") from e

    limits = _parse_limits(os.environ.get("PHASE1_RATE_LIMITS", "200 per minute"))
    storage_uri = os.environ.get("PHASE1_LIMITER_STORAGE_URI")  # optional (e.g., redis://...)

    kwargs = {"key_func": get_remote_address, "default_limits": limits}
    if storage_uri:
        kwargs["storage_uri"] = storage_uri

    limiter = Limiter(**kwargs)
    limiter.init_app(app)
    app.logger.info("Phase1: limiter enabled with %s", ", ".join(limits))
    return limiter
