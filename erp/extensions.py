# erp/extensions.py  (full replacement)
from flask_socketio import SocketIO

# Do not hardcode async_mode here; we set it during init to avoid bad env overrides.
socketio = SocketIO(cors_allowed_origins="*")
