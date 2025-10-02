# wsgi.py
from erp.app import create_app

app = create_app()

if __name__ == "__main__":
    # For local debugging only
    app.run(host="0.0.0.0", port=10000, debug=True)
