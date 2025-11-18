# Blueprint Registration Audit (Application Factory)

## Scope and method
- Bootstrapped the Flask application via `erp.create_app()` using default configuration to exercise built-in blueprint discovery and registration.
- Collected blueprint names from `app.blueprints` and compared against the expected modules produced by `_iter_blueprint_modules()` (which merges `blueprints_dedup_manifest.txt` and `_DEFAULT_BLUEPRINT_MODULES` with exclusions).
- Recorded runtime dependency warnings emitted during startup to flag missing optional integrations.

## Findings
- All expected blueprint modules were discoverable and successfully registered; `app.blueprints` includes: analytics, approvals, auth, crm, finance_api, health, hr, inventory_bp, maintenance, marketing, orders, report_builder, sales, ui, user_management, and web.
- No expected blueprint modules were missing during discovery.
- Startup reported that `Flask-Mail` and `Flask-Limiter` are not installed in the current environment, so email delivery and rate-limiting features are inactive. These dependencies are present in `requirements.lock`, so installing dependencies will restore the integrations.

## Recommendations
- Install the documented dependencies (e.g., via `pip install -r requirements.lock` or the project’s standard tooling) to enable mail delivery and rate limiting in non-test environments.
- Re-run the application bootstrap after dependency installation to confirm no additional warnings and to validate any environment-specific blueprints.
