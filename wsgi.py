import os
from erp import create_app

app = create_app(os.getenv("FLASK_CONFIG"))
