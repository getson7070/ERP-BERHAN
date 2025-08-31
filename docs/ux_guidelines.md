# UX Guidelines

This project follows industry-standard UX and accessibility practices:

- **Responsive design:** verify layouts across mobile (375px), tablet (768px), and desktop (1280px) viewports. Reference snapshots live in [`docs/ux/snapshots`](./ux/snapshots).
- **Accessible markup:** templates include semantic headings and ARIA labels. Automated checks run via `pa11y-ci` (best effort) and `axe`.
- **Dark mode:** toggle provided with persistent preference stored in `localStorage`.
- **Form validation:** Bootstrap validation styles used with `needs-validation` class and custom scripts to ensure keyboard and screen reader support.
- **CSP nonces:** all inline scripts/styles use `csp_nonce()` to align with our Content Security Policy.
- **PWA support:** service worker and web app manifest enable offline access and installable experience on mobile.

Developers should run:

```bash
npx pa11y-ci templates/base.html || true  # requires Chromium dependencies
pytest tests/test_template_accessibility.py::test_base_template_axe
```

before committing frontend changes to catch regressions.

See [Cross-Browser and Accessibility Audit](./browser_accessibility_review.md) for a full checklist covering browser compatibility, manual accessibility review, service worker and CSP verification, database integrity, and ongoing maintenance.

Supported browser versions are tracked in [browser_matrix.md](./browser_matrix.md), and outcomes of manual accessibility reviews belong in [accessibility_audit_log.md](./accessibility_audit_log.md).
