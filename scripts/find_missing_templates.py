"""Detect missing Jinja templates referenced by Flask routes.

The script now gathers route metadata (blueprint name, rule, HTTP methods) so
that remediation work can be triaged per domain module.
"""
from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "erp"
TEMPLATE_DIRS = [ROOT / "erp" / "templates", ROOT / "templates"]
UNMAPPED_BLUEPRINT = "<unmapped>"


@dataclass(frozen=True)
class RouteContext:
    blueprint: str | None
    rule: str | None
    methods: tuple[str, ...] | None


@dataclass(frozen=True)
class MissingTemplateRecord:
    template: str
    source: Path
    function: str | None
    routes: tuple[RouteContext, ...]


def template_exists(template: str) -> bool:
    for base in TEMPLATE_DIRS:
        candidate = base / template
        if candidate.exists():
            return True
    return False


def _get_root_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _get_root_name(node.value)
    return None


def _parse_methods(node: ast.AST) -> tuple[str, ...] | None:
    if isinstance(node, (ast.List, ast.Tuple)):
        values: list[str] = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                values.append(elt.value)
        if values:
            return tuple(values)
    return None


class TemplateCollector(ast.NodeVisitor):
    """Collect render_template calls with contextual route metadata."""

    def __init__(self, py_path: Path, root: Path) -> None:
        self.py_path = py_path
        self.root = root
        self.function_stack: list[ast.AST] = []
        self.route_contexts: dict[ast.AST, tuple[RouteContext, ...]] = {}
        self.blueprints: dict[str, str | None] = {}
        self.missing: list[MissingTemplateRecord] = []

    # --- Node visitors -------------------------------------------------
    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: D401
        """Capture blueprint variable assignments."""

        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == "Blueprint":
                blueprint_name = None
                if node.value.args and isinstance(node.value.args[0], ast.Constant):
                    value = node.value.args[0].value
                    if isinstance(value, str):
                        blueprint_name = value
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.blueprints[target.id] = blueprint_name
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._register_route_contexts(node)
        self.function_stack.append(node)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._register_route_contexts(node)
        self.function_stack.append(node)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        template = self._extract_template_literal(node)
        if template and not template_exists(template):
            function_name = None
            if self.function_stack:
                top = self.function_stack[-1]
                if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_name = top.name
            routes: tuple[RouteContext, ...] = ()
            for func in reversed(self.function_stack):
                if func in self.route_contexts:
                    routes = self.route_contexts[func]
                    break
            record = MissingTemplateRecord(
                template=template,
                source=self.py_path.relative_to(self.root),
                function=function_name,
                routes=routes,
            )
            self.missing.append(record)
        self.generic_visit(node)

    # --- Helpers -------------------------------------------------------
    def _register_route_contexts(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        contexts: list[RouteContext] = []
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute) or func.attr != "route":
                continue
            blueprint_var = _get_root_name(func.value)
            blueprint_name = self.blueprints.get(blueprint_var or "", blueprint_var)
            rule: str | None = None
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                arg_value = decorator.args[0].value
                if isinstance(arg_value, str):
                    rule = arg_value
            if rule is None:
                for keyword in decorator.keywords:
                    if keyword.arg == "rule" and isinstance(keyword.value, ast.Constant):
                        kw_value = keyword.value.value
                        if isinstance(kw_value, str):
                            rule = kw_value
            methods: tuple[str, ...] | None = None
            for keyword in decorator.keywords:
                if keyword.arg == "methods":
                    methods = _parse_methods(keyword.value)
                    break
            contexts.append(
                RouteContext(
                    blueprint=blueprint_name,
                    rule=rule,
                    methods=methods,
                )
            )
        if contexts:
            self.route_contexts[node] = tuple(contexts)

    @staticmethod
    def _extract_template_literal(node: ast.Call) -> str | None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "render_template":
            args = node.args
            if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                return args[0].value
        elif isinstance(func, ast.Name) and func.id == "render_template":
            args = node.args
            if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                return args[0].value
        return None


def collect_missing_templates() -> dict[str, list[MissingTemplateRecord]]:
    missing: dict[str, set[MissingTemplateRecord]] = {}
    for py_file in SOURCE_ROOT.rglob("*.py"):
        code = py_file.read_text("utf-8")
        try:
            tree = ast.parse(code, filename=str(py_file))
        except SyntaxError:
            continue
        collector = TemplateCollector(py_file, ROOT)
        collector.visit(tree)
        for record in collector.missing:
            missing.setdefault(record.template, set()).add(record)
    sorted_missing: dict[str, list[MissingTemplateRecord]] = {}
    for template, records in missing.items():
        sorted_missing[template] = sorted(
            records,
            key=lambda r: (
                str(r.source),
                r.function or "",
                tuple(
                    (ctx.blueprint or "", ctx.rule or "", ctx.methods or ())
                    for ctx in r.routes
                ),
            ),
        )
    return sorted_missing


def _format_methods(route: RouteContext) -> str:
    if route.methods:
        return ", ".join(route.methods)
    return "GET"


def main() -> int:
    missing = collect_missing_templates()
    if not missing:
        print("No missing templates detected.")
        return 0
    total_missing = len(missing)
    grouped_templates: dict[str, set[str]] = defaultdict(set)
    print("Missing templates:")
    for template in sorted(missing):
        print(f"- {template}")
        seen_blueprints = False
        for record in missing[template]:
            print(f"    referenced from: {record.source}")
            if record.function:
                print(f"        function: {record.function}")
            if record.routes:
                for route in record.routes:
                    blueprint = route.blueprint or "<unknown>"
                    rule = route.rule or "<unspecified>"
                    methods = _format_methods(route)
                    print(
                        "        route: "
                        f"blueprint='{blueprint}' rule='{rule}' methods={methods}"
                    )
                    grouped_templates[blueprint].add(template)
                    seen_blueprints = True
        if not seen_blueprints:
            grouped_templates[UNMAPPED_BLUEPRINT].add(template)
    print(f"Total missing templates: {total_missing}")
    if grouped_templates:
        print("\nSummary by blueprint:")
        for blueprint, templates in sorted(
            grouped_templates.items(), key=lambda item: (-len(item[1]), item[0])
        ):
            print(f"- {blueprint}: {len(templates)} template(s) missing")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
