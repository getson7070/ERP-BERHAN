*** a/wsgi.py
--- b/wsgi.py
@@
-# entrypoint for gunicorn
-from erp.app import app
+# IMPORTANT: Patch before importing anything that uses sockets/threads
+import eventlet
+eventlet.monkey_patch()
+
+# entrypoint for gunicorn
+from erp.app import app
