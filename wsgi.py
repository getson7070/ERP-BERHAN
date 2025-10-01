# >>> this must be at the very top, before any other imports <<<
import eventlet
eventlet.monkey_patch()

from erp.app import create_app
app = create_app()
