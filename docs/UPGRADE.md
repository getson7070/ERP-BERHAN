# ERP-BERHAN Upgrade Pack (additive)

## Wire-up (one-time)
Edit your app factory (e.g., `erp/app.py`):

```python
from erp.security.headers import init_security_headers
from erp.device_trust.blueprint import bp as device_bp

def create_app():
    app = Flask(__name__)
    # ... your setup ...
    init_security_headers(app)
    app.register_blueprint(device_bp)
    return app
```

## Run locally
```powershell
powershell -ExecutionPolicy Bypass -File scripts\reset-dev.ps1 -HardReset
```

Open http://localhost:18000

### Test accounts
- Admin: `admin@local.test` / `Dev!23456`
- Employee: `emp1@local.test` / `Pass!12345`
- Client: `client1@local.test` / `Pass!12345`
