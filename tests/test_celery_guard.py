import pytest

from erp.security_celery_guard import RBACGuardedTask


class _DeniedTask(RBACGuardedTask):
    required_permission = ("finance.close", "run")

    def run(self, *args, **kwargs):  # pragma: no cover - not expected to run
        return "ok"


def test_celery_guard_blocks_without_permission(resolve_org_id):
    task = _DeniedTask()

    with pytest.raises(PermissionError):
        task(org_id=resolve_org_id(), actor_id=999)
