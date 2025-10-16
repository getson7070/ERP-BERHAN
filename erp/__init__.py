# erp/__init__.py
from flask import Flask
from erp.extensions import init_extensions  # <-- add this import

def create_app():
    app = Flask(__name__)
    # ... your existing config & setup ...

    init_extensions(app)  # <-- add this line

    # ... register blueprints, etc. ...
    return app
