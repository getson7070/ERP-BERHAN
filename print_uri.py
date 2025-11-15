import os
from erp import create_app
app = create_app()
print("ENV DATABASE_URL =", os.environ.get("DATABASE_URL"))
print("ENV SQLALCHEMY_DATABASE_URI =", os.environ.get("SQLALCHEMY_DATABASE_URI"))
print("APP SQLALCHEMY_DATABASE_URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))
