--- a/app.py
+++ b/app.py
@@
 from flask import Flask
-from erp.models import db
+from erp.models import db
+from erp.extensions import limiter
+from werkzeug.middleware.proxy_fix import ProxyFix

 def create_app():
     app = Flask(__name__)
     app.config.from_prefixed_env()  # FLASK_* or APP_*

+    # Secure session cookies (prod values via env config)
+    app.config.setdefault("SESSION_COOKIE_SECURE", True)
+    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
+    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
+    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # respect reverse proxy for HTTPS

     db.init_app(app)
+    limiter.init_app(app)

     # set global security headers
     @app.after_request
     def set_headers(resp):
         resp.headers.setdefault("X-Content-Type-Options", "nosniff")
         resp.headers.setdefault("X-Frame-Options", "DENY")
         resp.headers.setdefault("Referrer-Policy", "no-referrer")
         resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
         return resp
     return app
