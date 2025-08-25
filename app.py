"""WSGI entry point for BERHAN ERP."""

from erp import create_app

app = create_app()
app.config["TEMPLATES_AUTO_RELOAD"] = True

if __name__ == '__main__':
    app.run()
