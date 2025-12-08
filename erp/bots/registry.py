"""Central registration for built-in Telegram bot commands.

This module keeps command wiring in one place so the dispatcher always has a
complete map of intents to handlers. It is intentionally idempotent so
`create_app` can call it during boot without worrying about duplicate
registrations when tests spin up multiple Flask apps.
"""
from __future__ import annotations

from erp.bots import register_command
from erp.bots.handlers import (
    analytics_query,
    approve_action,
    help_menu,
    inventory_query,
    reject_action,
    whoami,
)

_REGISTERED = False


def register_default_bot_commands() -> None:
    """Register the core set of bot commands if not already registered."""

    global _REGISTERED
    if _REGISTERED:
        return

    register_command("help", help_menu)
    register_command("whoami", whoami)

    # Sensitive actions stay locked to admins by default to avoid accidental
    # privilege escalation in chat. Additional roles can be granted through the
    # RBAC console if needed.
    register_command("approve_action", approve_action, required_role="admin")
    register_command("reject_action", reject_action, required_role="admin")

    # Informational queries remain open to authenticated bot users; downstream
    # RBAC rules on the API surface still apply when handlers touch the DB.
    register_command("inventory_query", inventory_query)
    register_command("analytics_query", analytics_query)

    _REGISTERED = True


__all__ = ["register_default_bot_commands"]
