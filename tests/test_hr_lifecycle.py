import datetime as dt

import pytest


def _auth_headers_for(role_user):
    # TODO: replace with helper that returns Authorization headers for the test client
    return {}


@pytest.mark.parametrize("role", ["hr", "admin"])
def test_create_employee_and_onboarding(client, db_session, make_user_with_role, role):
    user = make_user_with_role(role)
    headers = _auth_headers_for(user)

    # 1) Create employee
    resp = client.post(
        "/hr/employees",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test.hr@example.com",
            "role": "staff",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    employee = resp.get_json()
    emp_id = employee["id"]

    # 2) Add onboarding record
    today = dt.date.today().isoformat()
    resp = client.post(
        f"/hr/employees/{emp_id}/onboarding",
        json={
            "start_date": today,
            "contract_type": "permanent",
            "checklist": {"contract_signed": True},
            "completed": False,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["employee_id"] == emp_id
    assert data["contract_type"] == "permanent"


def test_leave_request_self_service_and_approval(
    client, db_session, make_employee_user, make_user_with_role
):
    # Employee user
    employee_user, employee = make_employee_user()
    emp_headers = _auth_headers_for(employee_user)

    # HR admin
    hr_user = make_user_with_role("hr")
    hr_headers = _auth_headers_for(hr_user)

    start = dt.date.today()
    end = start + dt.timedelta(days=2)

    # Employee creates leave request
    resp = client.post(
        f"/hr/employees/{employee.id}/leave",
        json={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "leave_type": "annual",
            "reason": "Family event",
        },
        headers=emp_headers,
    )
    assert resp.status_code == 201
    leave = resp.get_json()
    leave_id = leave["id"]
    assert leave["status"] == "pending"

    # HR approves
    resp = client.post(
        f"/hr/leave/{leave_id}/decision",
        json={"decision": "approved"},
        headers=hr_headers,
    )
    assert resp.status_code == 200
    leave2 = resp.get_json()
    assert leave2["status"] == "approved"
    assert leave2["approver_id"] == hr_user.id
