#!/usr/bin/env python3
import json
import sys
from typing import Union, Sequence

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


def main() -> None:
    app = create_app()
    csp = app.extensions["talisman"].content_security_policy
    policy = _flatten(csp)
    resp = requests.get(
        "https://csp-evaluator.withgoogle.com/api/csp",
        params={"csp": policy},
        timeout=10,
    )
    data = resp.json()
    if data.get("warnings") or data.get("errors"):
        print(json.dumps(data))
        sys.exit(1)
    print("CSP OK")


if __name__ == "__main__":
    main()
