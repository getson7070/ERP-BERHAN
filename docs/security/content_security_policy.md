# Content Security Policy

The application enforces a strict Content Security Policy using
[`Flask-Talisman`](https://github.com/GoogleCloudPlatform/flask-talisman).
The default policy only allows resources to load from the same origin:

```
{
  "default-src": "'self'"
}
```

Adjust the policy via `Talisman` in `erp/__init__.py` if additional
resources are required. Review changes with security to ensure third-party
scripts are trusted.
