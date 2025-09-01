"""Validate Content Security Policy without relying on remote services.

The original implementation posted the policy to Google's CSP evaluator API.
That external call occasionally returns ``404`` or times out which caused the
script to emit a warning in CI.  To keep the check reliable and self-contained
we now perform a small set of static validations locally and only attempt the
remote request when explicitly configured via ``CSP_EVAL_URL``.
"""

import json
import os
import sys
from typing import Sequence, Union

import requests

from erp import create_app, talisman


def _flatten(policy: dict[str, Union[Sequence[str], str]]) -> str:
    parts: list[str] = []
    for key, value in policy.items():
        if isinstance(value, (list, tuple, set)):
            val = " ".join(value)
        else:
            val = str(value)
        parts.append(f"{key} {val}")
    return "; ".join(parts)


def _policy_from_url(url: str) -> str:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    csp = resp.headers.get("content-security-policy")
    if not csp:
        raise RuntimeError("No CSP header present")
    return csp


def _policy_from_app() -> str:
    """Render the CSP defined by the Flask application.

    ``create_app`` touches the database to seed default roles which fails when
    the schema has not yet been created.  Running in testing mode triggers a
    ``create_all`` so the in-memory tables exist just long enough for the CSP
    to be built.
    """

    os.environ.setdefault("PYTEST_CURRENT_TEST", "validate_csp")
    create_app()
    return _flatten(talisman.content_security_policy)


def _evaluate(policy: str) -> int:
    """Validate the provided CSP string.

    If ``CSP_EVAL_URL`` is defined, the policy is sent to that endpoint and any
    warnings or errors cause the script to fail.  When the variable is unset or
    the request fails, we fall back to lightweight local checks that look for
    obviously unsafe directives.  The fallback keeps CI green even when the
    network or external service is unavailable.
    """

    remote_url = os.getenv("CSP_EVAL_URL")
    if remote_url:
        try:
            resp = requests.post(remote_url, json={"csp": policy}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("warnings") or data.get("errors"):
                print(json.dumps(data, indent=2))
                return 1
            print("CSP validated with no warnings")
            return 0
        except Exception as exc:
            print(f"Remote CSP evaluator failed: {exc}; running basic checks")

    if any(token in policy for token in ["'unsafe-inline'", "'unsafe-eval'"]):
        print("CSP contains unsafe directives")
        return 1
    print("CSP validation completed with basic checks")
    return 0


def main() -> int:
    policy = _policy_from_url(sys.argv[1]) if len(sys.argv) == 2 else _policy_from_app()
    return _evaluate(policy)


if __name__ == "__main__":
    sys.exit(main())
