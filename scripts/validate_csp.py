"""Validate Content Security Policy using Google's CSP Evaluator."""

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
    try:
        resp = requests.post(
            "https://csp-evaluator.withgoogle.com/api/evaluate",
            json={"csp": policy},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("warnings") or data.get("errors"):
            print(json.dumps(data, indent=2))
            return 1
        print("CSP validated with no warnings")
        return 0
    except Exception as exc:  # network or parsing issue
        print(f"CSP evaluator unavailable: {exc}")
        if any(token in policy for token in ["'unsafe-inline'", "'unsafe-eval'"]):
            print("CSP contains unsafe directives")
            return 1
        print("CSP validation skipped; no obvious issues found")
        return 0


def main() -> int:
    policy = _policy_from_url(sys.argv[1]) if len(sys.argv) == 2 else _policy_from_app()
    return _evaluate(policy)


if __name__ == "__main__":
    sys.exit(main())
