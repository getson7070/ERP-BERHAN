import eventlet
eventlet.monkey_patch()

from erp.app import create_app  # import AFTER monkey_patch
app = create_app()

if __name__ == "__main__":
    app.run()
