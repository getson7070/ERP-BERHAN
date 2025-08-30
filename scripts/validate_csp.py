"""Validate Content Security Policy using Google's CSP Evaluator."""

import json
import sys
from typing import Sequence, Union

import requests

from erp import create_app


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
    app = create_app()
    csp = app.extensions["talisman"].content_security_policy
    return _flatten(csp)


def _evaluate(policy: str) -> int:
    resp = requests.post(
        "https://csp-evaluator.withgoogle.com/api/evaluate",
        json={"csp": policy},
        timeout=10,
    )
    data = resp.json()
    if data.get("warnings") or data.get("errors"):
        print(json.dumps(data, indent=2))
        return 1
    print("CSP validated with no warnings")
    return 0


def main() -> int:
    policy = _policy_from_url(sys.argv[1]) if len(sys.argv) == 2 else _policy_from_app()
    return _evaluate(policy)


if __name__ == "__main__":
    sys.exit(main())
