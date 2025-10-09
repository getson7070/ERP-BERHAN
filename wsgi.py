# >>> MUST be first line when using eventlet workers <<<
import eventlet
eventlet.monkey_patch()

from erp import create_app

# Gunicorn will import "wsgi:app"
app = create_app()
