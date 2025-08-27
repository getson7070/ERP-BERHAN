# Templates

All pages extend `templates/base.html` for a consistent layout and include the shared navbar from `partials/navbar.html`.

Use the `content` block for page-specific markup. Templates that still use the older `body` block remain compatible.

Error pages live under `templates/errors/` and provide basic 401, 403, 404, and 500 views.
