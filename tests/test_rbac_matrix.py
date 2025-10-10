import pytest
import itertools

ROLES = ["admin","manager","employee"]
ACTIONS = [
  ("hr.view_employee", {"should": ["admin","manager"]}),
  ("hr.edit_employee", {"should": ["admin"]}),
  ("crm.view_customer", {"should": ["admin","manager","employee"]}),
  ("crm.edit_customer", {"should": ["admin","manager"]}),
]

@pytest.mark.parametrize("role,action", itertools.product(ROLES, [a for a,_ in ACTIONS]))
def test_rbac_enforcement(client, role, action, login_as_role):
    login_as_role(role)
    resp = client.get(f"/permcheck?name={action}")
    allowed = next(s for a,s in ACTIONS if a==action)["should"]
    assert (resp.status_code == 200) == (role in allowed)
