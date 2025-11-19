"""Create hashed invite codes for secure self-service registration."""
from __future__ import annotations

import argparse
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from erp import create_app
from erp.models import RegistrationInvite, db


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="Optional email to scope the invite")
    parser.add_argument("--role", default="employee", help="Role granted when redeeming the invite")
    parser.add_argument("--uses", type=int, default=1, help="How many times the invite can be redeemed")
    parser.add_argument(
        "--ttl-hours",
        type=int,
        default=72,
        help="Number of hours before the invite expires. Use 0 for no expiry.",
    )
    args = parser.parse_args()

    token = secrets.token_urlsafe(24)
    expires_at = None
    if args.ttl_hours:
        expires_at = datetime.now(UTC) + timedelta(hours=args.ttl_hours)

    app = create_app()
    with app.app_context():
        invite = RegistrationInvite(
            token_hash=_hash_token(token),
            email=args.email,
            role=args.role.lower(),
            uses_remaining=max(1, args.uses),
            expires_at=expires_at,
        )
        db.session.add(invite)
        db.session.commit()
        print("Invite created for role", invite.role)
        if invite.email:
            print("Restricted to", invite.email)
        if expires_at:
            print("Expires at", expires_at.isoformat())
        print("Share this token securely:", token)


if __name__ == "__main__":
    main()
