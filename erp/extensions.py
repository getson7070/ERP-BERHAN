from flask_sqlalchemy import SQLAlchemy

# Central place to instantiate extensions to avoid circular imports.
# Additional extensions can be added here as the application grows.
db = SQLAlchemy()
