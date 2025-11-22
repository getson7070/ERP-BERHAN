from erp.extensions import db
from erp.models import RBACPolicy, RBACPolicyRule
from erp.security_rbac_phase2 import invalidate_policy_cache, is_allowed


def test_deny_overrides_allow(db_session, resolve_org_id):
    org_id = resolve_org_id()

    policy = RBACPolicy(org_id=org_id, name="store_policy", priority=1)
    db.session.add(policy)
    db.session.flush()

    db.session.add(
        RBACPolicyRule(
            org_id=org_id,
            policy_id=policy.id,
            role_key="storekeeper",
            resource="inventory.stock",
            action="adjust",
            effect="allow",
        )
    )
    db.session.add(
        RBACPolicyRule(
            org_id=org_id,
            policy_id=policy.id,
            role_key="storekeeper",
            resource="inventory.stock",
            action="adjust",
            effect="deny",
        )
    )
    db.session.commit()
    invalidate_policy_cache()

    assert is_allowed(org_id, ["storekeeper"], "inventory.stock", "adjust") is False
