"""Detect missing Jinja templates referenced by Flask routes."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "erp" / "templates"
SOURCE_ROOT = ROOT / "erp"


def collect_missing_templates() -> dict[str, set[str]]:
    missing: dict[str, set[str]] = {}
    for py_file in SOURCE_ROOT.rglob("*.py"):
        code = py_file.read_text("utf-8")
        try:
            tree = ast.parse(code, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "render_template":
                args = node.args
                if not args or not isinstance(args[0], ast.Constant) or not isinstance(args[0].value, str):
                    continue
                template = args[0].value
            elif isinstance(func, ast.Name) and func.id == "render_template":
                args = node.args
                if not args or not isinstance(args[0], ast.Constant) or not isinstance(args[0].value, str):
                    continue
                template = args[0].value
            else:
                continue
            template_path = TEMPLATE_ROOT / template
            if not template_path.exists():
                missing.setdefault(template, set()).add(str(py_file.relative_to(ROOT)))
    return missing


def main() -> int:
    missing = collect_missing_templates()
    if not missing:
        print("No missing templates detected.")
        return 0
    print("Missing templates:")
    for template in sorted(missing):
        print(f"- {template}")
        for src in sorted(missing[template]):
            print(f"    referenced from: {src}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
