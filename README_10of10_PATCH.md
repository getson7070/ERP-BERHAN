# ERP 10/10 Patch

This patch gets you to **production-ready** status by addressing:
- Guaranteed blueprint registration with **import-failure diagnostics**
- Inventory **Delivery/Issue** endpoint (negative SLE posting)
- Minimal **Banking** (upload/reconcile) UI
- Minimal **CRM Pipeline** UI
- **RBAC** decorator for role-gated routes
- Admin **Diagnostics** pages to verify runtime status
- Migration **baseline reset** instructions

## Files

- `erp/__init__.py` — app factory with autodiscovery & logging
- `erp/observability/diagnostics.py` + `erp/templates/admin/diagnostics.html`
- `erp/inventory/routes_delivery.py`
- `erp/finance/banking.py` + templates
- `erp/crm/pipeline.py` + template
- `erp/security/rbac.py`
- `scripts/migrations/BASELINE_RESET.md`

## How to apply

1) Copy files to your repo root (preserve paths).  
2) Restart your app. Visit:
   - `/healthz` — should show a long list of registered blueprints.
   - `/admin/diagnostics` — see **Registered Blueprints** and **Import Failures** (must be empty).

3) **Migrations**: follow `scripts/migrations/BASELINE_RESET.md` to create a fresh **single-head** baseline.  
   - After baseline, the Banking tables will be created automatically via `alembic --autogenerate` if models remain in place.

4) **Inventory**:
   - `POST /inventory/grn` — stock in (existing).
   - `POST /inventory/delivery` — stock out (new).  
   - `GET /inventory/onhand/<item>/<warehouse>` — should reflect both.

5) **Security/RBAC (optional)**:
   - Protect sensitive routes:  
     ```python
     from erp.security.rbac import require_roles

     @some_bp.route("/finance-only")
     @login_required
     @require_roles("accountant", "admin")
     def finance_only():
         ...
     ```

6) **Smoke checklist**:
   - `/finance/banking` loads; you can upload a CSV (date,description,amount) and view **/finance/banking/reconcile**.
   - `/crm/pipeline` loads.
   - `/admin/blueprints` returns JSON of all mounted blueprints.
   - `/admin/import_failures` returns `[]`.

## Notes
- Patch is **non-destructive**; it won’t break existing routes.  
- If any module still doesn’t show up in diagnostics, there is an **import-time error**; fix it and it will mount automatically.

