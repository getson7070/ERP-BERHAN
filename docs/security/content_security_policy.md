# Content Security Policy

The application enforces a strict Content Security Policy using
[`Flask-Talisman`](https://github.com/GoogleCloudPlatform/flask-talisman).
All third-party libraries are self-hosted under `/static/vendor`, so the
policy only allows resources from the application itself and injects
per-request nonces for inline scripts and styles:

```
{
  "default-src": "'self'",
  "script-src": ["'self'"],
  "style-src": ["'self'"],
  "img-src": ["'self'", "data:"],
  "connect-src": ["'self'"],
  "font-src": ["'self'"],
  "frame-ancestors": "'none'"
}
```

Inline `<script>` and `<style>` tags must include `nonce="{{ csp_nonce() }}"`
so the browser can verify they originate from the application. External
assets from whitelisted CDNs should specify Subresource Integrity (SRI)
hashes to prevent tampering.

Adjust the policy via `Talisman` in `erp/__init__.py` if additional
origins are needed. Review changes with security to ensure third‑party
scripts are trusted.
