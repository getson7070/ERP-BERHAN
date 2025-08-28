# Templates

All pages extend `templates/base.html` for a consistent layout and include the shared navbar from `partials/navbar.html`.

Use the `content` block for page-specific markup. Templates that still use the older `body` block remain compatible.

Error pages live under `templates/errors/` and provide basic 401, 403, 404, and 500 views.

## Accessibility & Tours
- Pages must pass WCAG 2.1 AA checks using the `npm run lint:accessibility` script powered by `axe`.
- Role-based dashboards support per-user widget layouts saved in `dashboard_layouts`.
- The `docs/in_app_help.md` runbook covers onboarding tours surfaced via the `intro.js` library.

## Interactive Features
- Tables support inline row editing and saved filter presets via URL query strings.
- Barcode scanning uses the `quagga` library; see `static/js/barcode.js` for integration details.
- A Kanban board view is available at `/workflow/kanban` with SLA timers and escalation rules documented in `docs/automation_analytics.md`.
