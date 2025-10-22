from erp.api.integrations import create_app
from erp.bootstrap_phase1 import apply_phase1_hardening

app = create_app()
apply_phase1_hardening(app)
