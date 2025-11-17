# Templates

All pages extend `erp/templates/base.html` for a consistent layout and include the shared navbar from `erp/templates/partials/navbar.html`.

Use the `content` block for page-specific markup. Templates that still use the older `body` block remain compatible.

Error pages live under `templates/errors/` and provide basic 401, 403, 404, and 500 views.

## Design System

Templates should use spacing and typography tokens defined in
[docs/design_system.md](design_system.md) to maintain consistent UI and
responsive layouts.

Inline scripts and styles must include
`nonce="{{ csp_nonce() }}"` to comply with the Content Security Policy.
External assets loaded from approved CDNs should include Subresource
Integrity hashes.
