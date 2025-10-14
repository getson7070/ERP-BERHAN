from flask import current_app
from flask_wtf.csrf import generate_csrf

def register_context_processors(app):
    @app.context_processor
    def inject_csrf():
        # Ensures {{ csrf_token() }} works in Jinja even without WTForms Form instance
        return {"csrf_token": generate_csrf}
