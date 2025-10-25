from erp.app import create_app
from erp.db import db
from erp.models.user import User
from erp.security import hash_password

USERS = [
    ("admin@local.test", "Dev!23456", "admin"),
    ("employee@local.test", "Emp!23456", "employee"),
    ("client@local.test", "Cli!23456", "client"),
]

def ensure_user(email, raw_password, role):
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(email=email, role=role, is_active=True)
        u.password_hash = hash_password(raw_password)
        db.session.add(u)
        db.session.commit()
        print(f"created: {email} ({role})")
    else:
        changed = False
        if u.role != role:
            u.role = role
            changed = True
        # Always reset password for deterministic testing
        u.password_hash = hash_password(raw_password)
        changed = True
        if changed:
            db.session.commit()
            print(f"updated: {email} ({role})")
        else:
            print(f"exists: {email}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for args in USERS:
            ensure_user(*args)
        print("OK")
