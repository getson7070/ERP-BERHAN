# scripts/seed_accounts.py
import os
from erp.app import create_app
from erp.db_session import get_session
from erp.models.user import User, Role
from sqlalchemy import select

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL","admin@local.test")
EMP_EMAIL = os.getenv("EMP_EMAIL","employee@local.test")
CLIENT_EMAIL = os.getenv("CLIENT_EMAIL","client@local.test")
DEFAULT_PW = os.getenv("DEFAULT_PW","Dev!23456")

app = create_app()
with app.app_context():
    with get_session() as s:
        def get_or_create_role(name):
            r = s.scalars(select(Role).where(Role.name==name)).first()
            if not r:
                r = Role(name=name)
                s.add(r); s.flush()
            return r
        admin_r = get_or_create_role("admin")
        emp_r = get_or_create_role("employee")
        client_r = get_or_create_role("client")

        def upsert(email, role):
            u = s.scalars(select(User).where(User.email==email)).first()
            if not u:
                u = User(email=email, role_id=role.id)
                u.set_password(DEFAULT_PW)
                s.add(u)
            else:
                u.role_id = role.id
            return u

        upsert(ADMIN_EMAIL, admin_r)
        upsert(EMP_EMAIL, emp_r)
        upsert(CLIENT_EMAIL, client_r)
        s.commit()
print("Seeded: admin/employee/client")
