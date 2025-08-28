# Plugin API and Versioning Policy

- **API Specification**: Plugins implement `register(app)` and may expose blueprints, CLI commands, and Celery tasks.
- **Versioning**: Semantic versioning is required; breaking changes increment the major version.
- **Compatibility Matrix**:

| Connector       | ERP Version | Status |
|----------------|-------------|--------|
| Accounting X   | >=1.0       | ✅     |
| E-commerce Y   | >=1.0       | ✅     |
| CRM Z          | >=1.1       | 🧪     |

- **Sandboxing**: Plugins run in isolated Python virtual environments and communicate over defined RPC interfaces.
- **Policy**: Public plugins must pass security scans and declare OAuth scopes.
