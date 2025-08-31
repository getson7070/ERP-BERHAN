"""Helpers for Microsoft Power BI integrations."""

import os


def get_embed_token() -> str:
    """Return a Power BI embed token from the environment.

    Raises:
        RuntimeError: If ``POWERBI_TOKEN`` is unset.
    """
    token = os.environ.get("POWERBI_TOKEN")
    if not token:
        raise RuntimeError("POWERBI_TOKEN is not configured")
    return token
