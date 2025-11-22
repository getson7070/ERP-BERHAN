"""LDAP/SSO group-to-role mapping helpers."""

from __future__ import annotations

import json
from typing import Iterable

from flask import current_app

from erp.services.role_service import grant_role_to_user


def apply_group_roles(org_id: int, user_id: int, groups: Iterable[str]) -> None:
    """Assign roles based on configured LDAP/OIDC group mappings."""

    raw_map = current_app.config.get("LDAP_GROUP_ROLE_MAP_JSON") or "{}"
    try:
        mapping = json.loads(raw_map)
    except Exception:
        mapping = {}

    for group in groups or []:
        role_key = mapping.get(group)
        if role_key:
            grant_role_to_user(org_id=org_id, user_id=user_id, role_key=role_key, acting_user=None)


__all__ = ["apply_group_roles"]
