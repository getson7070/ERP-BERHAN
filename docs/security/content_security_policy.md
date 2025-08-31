# Content Security Policy

The application enforces a strict Content Security Policy using
[`Flask-Talisman`](https://github.com/GoogleCloudPlatform/flask-talisman).
The policy enumerates permitted sources for each resource type and
injects a per-request nonce for inline scripts:

```
{
  "default-src": "'self'",
  "script-src": [
    "'self'",
    "https://cdn.jsdelivr.net",
    "https://cdn.socket.io"
  ],
  "style-src": [
    "'self'",
    "https://cdn.jsdelivr.net"
  ],
  "img-src": ["'self'", "data:"],
  "connect-src": ["'self'"],
  "frame-ancestors": "'none'"
}
```

Inline `<script>` tags must include `nonce="{{ csp_nonce() }}"` so the
browser can verify they originate from the application. External
assets from the CDNs above should specify Subresource Integrity (SRI)
hashes to prevent tampering.

Adjust the policy via `Talisman` in `erp/__init__.py` if additional
origins are needed. Review changes with security to ensure third‑party
scripts are trusted.
