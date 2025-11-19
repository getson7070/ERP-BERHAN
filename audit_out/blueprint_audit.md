# Blueprint Registration Audit (Application Factory)

## Scope and method
- Bootstrapped the Flask application via `erp.create_app()` using default configuration to exercise built-in blueprint discovery and registration.
- Enumerated `_DEFAULT_BLUEPRINT_MODULES` and `blueprints_dedup_manifest.txt`, imported each module, and verified every exposed `flask.Blueprint` instance is now auto-registered (modules no longer need to name the variable `bp`).
- Diffed the resulting `app.url_map` against customer-facing expectations (CRM, Marketing, Inventory, Supply Chain, Dashboard Customiser, Analytics, HR, Finance, Maintenance, Orders, and Reporting).
- Recorded runtime dependency warnings emitted during startup to flag missing optional integrations.

## Findings
- `register_blueprints` now inspects all module attributes and registers every `flask.Blueprint`, which fixed the gaps where modules exported `main_bp`, `dashboard_customize_bp`, `inventory_bp`, or `supply_bp` but not a `bp` alias. This guarantees that `/`, `/help`, `/feedback`, `/dashboard`, `/dashboard/customize`, `/reports/builder`, `/inventory/*`, `/supply/*`, `/analytics/dashboard`, `/finance/*`, `/orders/*`, `/crm/*`, `/hr/*`, `/maintenance/*`, and `/marketing/*` are mounted once the app starts.
- Verified that all modules listed in `_DEFAULT_BLUEPRINT_MODULES` import successfully and expose at least one blueprint. Overlapping modules (`erp.main` and `erp.routes.main`) now share the same `main` blueprint instance so intra-module routes remain linked and deduplicated.
- Startup reported that `Flask-Mail` and `Flask-Limiter` are not installed in the current environment, so email delivery and rate-limiting features are inactive. These dependencies are present in `requirements.lock`, so installing dependencies will restore the integrations.

## Verification commands
```
python - <<'PY'
from erp import create_app, _DEFAULT_BLUEPRINT_MODULES
app = create_app()
print('Blueprints:', sorted(app.blueprints))
print('Sample routes:', sorted(rule.rule for rule in app.url_map.iter_rules() if rule.rule in {'/','/dashboard','/dashboard/customize','/reports/builder','/inventory/','/supply/policy','/analytics/dashboard'}))
print('Default modules:', _DEFAULT_BLUEPRINT_MODULES)
PY
```

## Recommendations
- Install the documented dependencies (e.g., via `pip install -r requirements.lock` or the project’s standard tooling) to enable mail delivery and rate limiting in non-test environments.
- Re-run the application bootstrap after dependency installation to confirm no additional warnings and to validate any environment-specific blueprints.
