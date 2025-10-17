import eventlet
eventlet.monkey_patch()

from erp import create_app

app = create_app()

if __name__ == "__main__":
    # For local dev only
    app.run(host="0.0.0.0", port=5000, debug=True)

# === 9.8 patch: blueprint registrations (idempotent) ===
try:
    from erp.blueprints.finance import finance_bp
    app.register_blueprint(finance_bp)
except Exception as e:
    app.logger.warning(f"finance_bp not registered: {e}")

try:
    from erp.blueprints.integration import integration_bp
    app.register_blueprint(integration_bp)
except Exception as e:
    app.logger.warning(f"integration_bp not registered: {e}")

try:
    from erp.blueprints.recall import recall_bp
    app.register_blueprint(recall_bp)
except Exception as e:
    app.logger.warning(f"recall_bp not registered: {e}")

try:
    from erp.blueprints.bots import bots_bp
    app.register_blueprint(bots_bp)
except Exception as e:
    app.logger.warning(f"bots_bp not registered: {e}")
# === /9.8 patch ===
