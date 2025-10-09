# Template Coverage Audit

## Overview
Following the modernization of the UI theme, we audited the Flask blueprint routes to verify that every `render_template` call has a corresponding Jinja template. This review ensures the application can render all workflows without encountering missing-template errors that would degrade usability and reliability.

## Methodology
- Parsed every Python module beneath `erp/` looking for string literals passed to `render_template`.
- Normalized those template paths relative to `erp/templates/`.
- Flagged any template references without a matching file on disk.
- Spot-checked the template tree to confirm directory structures (e.g., `auth/`, `errors/`).

Re-run the audit with:

```bash
python3 scripts/find_missing_templates.py
```

or execute the embedded snippet below directly:

```bash
python3 - <<'PY'
import ast
from pathlib import Path
root = Path('erp')
missing = {}
for py_file in root.rglob('*.py'):
    code = py_file.read_text('utf-8')
    try:
        tree = ast.parse(code, filename=str(py_file))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == 'render_template':
                args = node.args
                if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                    template = args[0].value
                else:
                    continue
            elif isinstance(func, ast.Name) and func.id == 'render_template':
                args = node.args
                if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                    template = args[0].value
                else:
                    continue
            else:
                continue
            template_path = Path('erp/templates') / template
            if not template_path.exists():
                missing.setdefault(template, set()).add(str(py_file))
if not missing:
    print('No missing templates detected.')
else:
    print('Missing templates:')
    for tpl in sorted(missing):
        print(f'- {tpl}')
        for src in sorted(missing[tpl]):
            print(f'    referenced from: {src}')
PY
```

## Missing Templates
The following templates are referenced in application routes but are absent from `erp/templates/`. They should be implemented (or the routes adjusted) to avoid runtime `TemplateNotFound` errors.

| Template Path | Referenced From |
| --- | --- |
| `add_tender.html` | `erp/routes/tenders.py` |
| `admin/workflows.html` | `erp/routes/admin.py` |
| `crm/add.html` | `erp/routes/crm.py` |
| `crm/index.html` | `erp/routes/crm.py` |
| `customize_dashboard.html` | `erp/routes/dashboard_customize.py` |
| `feedback.html` | `erp/routes/feedback.py` |
| `finance/add.html` | `erp/routes/finance.py` |
| `finance/index.html` | `erp/routes/finance.py` |
| `help.html` | `erp/routes/help.py` |
| `hr/add.html` | `erp/routes/hr.py` |
| `hr/index.html` | `erp/routes/hr.py` |
| `hr/performance.html` | `erp/routes/hr_workflows.py` |
| `hr/recruitment.html` | `erp/routes/hr_workflows.py` |
| `inventory/index.html` | `erp/routes/inventory.py` |
| `kanban_board.html` | `erp/routes/kanban.py` |
| `manufacturing/add.html` | `erp/routes/manufacturing.py` |
| `manufacturing/index.html` | `erp/routes/manufacturing.py` |
| `orders.html` | `erp/routes/orders.py` |
| `orders_list.html` | `erp/routes/orders.py` |
| `plugins/index.html` | `erp/routes/plugins.py` |
| `plugins/marketplace.html` | `erp/routes/plugins.py` |
| `privacy.html` | `erp/routes/privacy.py` |
| `procurement/add.html` | `erp/routes/procurement.py` |
| `procurement/index.html` | `erp/routes/procurement.py` |
| `projects/add.html` | `erp/routes/projects.py` |
| `projects/index.html` | `erp/routes/projects.py` |
| `put_order.html` | `erp/routes/orders.py` |
| `receive_inventory.html` | `erp/routes/receive_inventory.py` |
| `report_builder.html` | `erp/routes/report_builder.py` |
| `tenders_list.html` | `erp/routes/tenders.py` |
| `tenders_report.html` | `erp/routes/tenders.py` |

## Recommended Next Steps
1. **Prioritize Critical Workflows** – Build templates for order management, procurement, finance, and inventory first to restore core ERP functionality.
2. **Align With Design System** – Ensure new templates adopt the modernized base layout, responsive breakpoints, and accessibility tokens from the refreshed design system.
3. **Integrate Security Controls** – Include CSRF tokens, form validation feedback, and RBAC-aware navigation within each template to maintain security posture.
4. **Coordinate With Backend** – Verify corresponding route logic, forms, and database interactions are production-ready before enabling the templates.
5. **Add Regression Coverage** – Once templates exist, extend integration tests or smoke tests to confirm each route renders successfully within CI.
