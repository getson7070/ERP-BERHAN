#!/usr/bin/env python
"""Unified registry scanner for blueprints, Celery tasks, and CLI commands.

Supports a safe mode via ``REGISTRY_SCAN_SKIP_APP=1`` to avoid failing on
broken local environments (for CI pre-flight this should stay unset).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "ops"
OPS.mkdir(exist_ok=True)

SCAN_OUT = OPS / "registry_scan.json"
MANIFEST = OPS / "registry_manifest.json"


class RegistryScanError(RuntimeError):
    """Raised when the registry scan detects a structural problem."""


def _load_app():
    from importlib import import_module

    module = import_module("erp")
    if not hasattr(module, "create_app"):
        raise RegistryScanError("erp.create_app is not available")
    return module.create_app()


def _scan_flask(app) -> tuple[list[dict[str, Any]], list[str]]:
    routes: list[dict[str, Any]] = []
    seen = set()
    duplicates: list[str] = []

    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        blueprint = endpoint.split(".", 1)[0] if "." in endpoint else None
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})

        if endpoint in seen:
            duplicates.append(endpoint)
        seen.add(endpoint)

        routes.append(
            {
                "endpoint": endpoint,
                "rule": str(rule),
                "methods": methods,
                "blueprint": blueprint,
            }
        )

    return routes, duplicates


def _scan_celery_tasks() -> tuple[list[dict[str, str | None]], list[str]]:
    try:
        from erp.celery_app import celery_app
    except Exception as exc:  # pragma: no cover - surfaced in tests via skip mode
        raise RegistryScanError(f"Unable to load celery_app: {exc}") from exc

    tasks: list[dict[str, str | None]] = []
    unnamed: list[str] = []

    for name, task in celery_app.tasks.items():
        if name.startswith("celery.") or name.startswith("__main__"):
            continue
        module = getattr(task, "__module__", None)
        tasks.append({"name": name, "module": module})
        if "." not in name:
            unnamed.append(name)
    return tasks, unnamed


def _scan_cli(app) -> tuple[list[dict[str, str]], list[str]]:
    ctx = app.test_cli_runner().get_default_context()
    commands: list[dict[str, str]] = []
    missing_tags: list[str] = []

    for cmd_name in app.cli.list_commands(ctx):
        commands.append({"name": cmd_name})
        cmd = app.cli.get_command(ctx, cmd_name)
        help_text = (cmd.help or "") + (cmd.short_help or "")
        if "[RBAC]" not in help_text and cmd_name not in {"routes", "shell"}:
            missing_tags.append(cmd_name)

    return commands, missing_tags


def _diff_manifest(manifest: dict, scan: dict) -> dict[str, Any]:
    def keyset(items: Iterable[dict[str, Any]], key: str) -> set[str]:
        return {str(item.get(key)) for item in items}

    def build_diff(kind: str) -> tuple[list[str], list[str]]:
        expected = keyset(manifest.get(kind, []), "endpoint" if kind == "flask_routes" else "name")
        current = keyset(scan.get(kind, []), "endpoint" if kind == "flask_routes" else "name")
        return sorted(current - expected), sorted(expected - current)

    new_routes, missing_routes = build_diff("flask_routes")
    new_tasks, missing_tasks = build_diff("celery_tasks")
    new_cmds, missing_cmds = build_diff("cli_commands")

    return {
        "new": {"routes": new_routes, "tasks": new_tasks, "commands": new_cmds},
        "missing": {"routes": missing_routes, "tasks": missing_tasks, "commands": missing_cmds},
        "has_errors": bool(missing_routes or missing_tasks),
    }


def _write_scan(scan: dict) -> None:
    SCAN_OUT.write_text(json.dumps(scan, indent=2), encoding="utf-8")
    print(f"Wrote {SCAN_OUT}")


def _safe_mode_output() -> dict:
    scan = {
        "flask_routes": [],
        "celery_tasks": [],
        "cli_commands": [],
        "issues": {"duplicate_endpoints": [], "celery_unnamespaced": [], "cli_missing_rbac_tag": []},
        "note": "REGISTRY_SCAN_SKIP_APP=1 set; populated minimal scan",
    }
    _write_scan(scan)
    return scan


def main() -> None:
    if os.getenv("REGISTRY_SCAN_SKIP_APP") == "1":
        _safe_mode_output()
        return

    try:
        app = _load_app()
        with app.app_context():
            flask_routes, dupes = _scan_flask(app)
            celery_tasks, bad_tasks = _scan_celery_tasks()
            cli_commands, cli_bad = _scan_cli(app)
    except Exception as exc:  # pragma: no cover - surfaced in CI, not unit test
        print(f"Registry scan failed to initialize: {exc}")
        raise SystemExit(1)

    scan = {
        "flask_routes": flask_routes,
        "celery_tasks": celery_tasks,
        "cli_commands": cli_commands,
        "issues": {
            "duplicate_endpoints": dupes,
            "celery_unnamespaced": bad_tasks,
            "cli_missing_rbac_tag": cli_bad,
        },
    }

    _write_scan(scan)

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        diff = _diff_manifest(manifest, scan)
        if diff["has_errors"]:
            print(json.dumps(diff, indent=2))
            raise SystemExit(1)

    if dupes or bad_tasks:
        print(json.dumps(scan["issues"], indent=2))
        raise SystemExit(2)

    print("Registry OK ✅")


if __name__ == "__main__":
    main()
