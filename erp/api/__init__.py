import erp.metrics_ext  # ensure graphql_rejects_total is registered
from .integrations import create_app, GRAPHQL_REJECTS, integrations_bp
