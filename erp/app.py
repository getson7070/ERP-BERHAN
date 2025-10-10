*** a/erp/app.py
--- b/erp/app.py
@@
-from flask import Flask
+from flask import Flask
+from flask_wtf import CSRFProtect
+from flask_limiter import Limiter
+from flask_limiter.util import get_remote_address
+import os
@@
-app = Flask(__name__, static_url_path="/static", static_folder="static")
+app = Flask(__name__, static_url_path="/static", static_folder="static")
+
+# --- Essentials ---
+# SECRET_KEY is required for CSRF/session. Pull from env or fall back to a temp key.
+app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-temp-key-change-me")
+
+# Rate limiter WITHOUT Redis (in-memory only, per your note)
+limiter = Limiter(
+    get_remote_address,
+    storage_uri="memory://",
+    app=app,
+)
+
+# Optional CSRF (keeps templates safe if you add forms later)
+csrf = CSRFProtect()
+csrf.init_app(app)
