# ERP-BERHAN Code and Intra-Module Connection Audit

**Updated:** 2025-02-16

## Remediation summary
- **Application factory unified.** `erp/__init__.py` now exposes a single `create_app` implementation that loads configuration consistently, binds shared extensions, applies the hardened security profile, and registers blueprints with duplicate protection. This removes the previously dead code paths and guarantees every environment boots with the same settings.
- **Shared inventory model restored.** The `Inventory` ORM class uses the repository-wide SQLAlchemy registry, enforces `(org_id, sku)` uniqueness, and surfaces helper methods (e.g., `tenant_query`, `to_dict`) so routes and services rely on the same metadata.
- **Inventory blueprint reinstated.** `erp/blueprints/inventory` publishes a single blueprint that validates payloads, scopes queries by organisation, paginates results, and exposes CRUD routes while preserving compatibility with existing helper imports. Duplicate modules and broken imports were removed.
- **Baseline UX refreshed.** The base layout and login template now present an industry-standard responsive shell with accessibility affordances, inline theming for dark mode, and CSRF-safe form scaffolding to unblock further screen work.

## Outstanding follow-ups
1. **Blueprint manifest hygiene.** The deduplicated manifest still carries legacy metadata; now that the loader fails gracefully on missing modules, normalise the manifest to relative modules and prune unused scaffolding.
2. **Module integration tests.** Add smoke tests that assert critical blueprints (analytics, inventory, dashboard) are reachable after registration to prevent regressions when new packages are added.
3. **Domain service hardening.** Align the remaining inventory service layers (e.g., exports, approvals) with the refreshed ORM model to ensure tenant scoping rules remain consistent.

## Testing recommendations
- Run targeted pytest suites covering inventory workflows and blueprint discovery (`tests/test_inventory.py`, `tests/test_blueprint_registration.py`).
- Execute Alembic autogeneration to verify the consolidated `Inventory` table definition matches production migrations.
- Perform UI smoke tests (manual or automated) to validate localisation selector behaviour and form CSRF tokens in the refreshed templates.
