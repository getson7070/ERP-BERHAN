from __future__ import annotations
from importlib import import_module
from flask import Blueprint

EXPLICIT_BLUEPRINTS = []  # list[tuple[Blueprint, str]]
try:
    _m = import_module("erp.routes._simple_bp")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "_simple_bp":
        EXPLICIT_BLUEPRINTS.append((_bp, "/_simple_bp"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.admin")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "admin":
        EXPLICIT_BLUEPRINTS.append((_bp, "/admin"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.admin_devices")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "admin_devices":
        EXPLICIT_BLUEPRINTS.append((_bp, "/admin_devices"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.analytics")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "analytics":
        EXPLICIT_BLUEPRINTS.append((_bp, "/analytics"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.api")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "api":
        EXPLICIT_BLUEPRINTS.append((_bp, "/api"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.auth")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "auth":
        EXPLICIT_BLUEPRINTS.append((_bp, "/auth"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.banking.routes")
    _bp = getattr(_m, "banking_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "banking":
        EXPLICIT_BLUEPRINTS.append((_bp, "/routes"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.bots")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "bots":
        EXPLICIT_BLUEPRINTS.append((_bp, "/bots"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.compliance")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "compliance":
        EXPLICIT_BLUEPRINTS.append((_bp, "/compliance"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.crm")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "crm":
        EXPLICIT_BLUEPRINTS.append((_bp, "/crm"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.crm.pipeline")
    _bp = getattr(_m, "crm_pipeline_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "crm_pipeline":
        EXPLICIT_BLUEPRINTS.append((_bp, "/pipeline"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.dashboard_customize")
    _bp = getattr(_m, "dashboard_customize_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "dashboard_customize":
        EXPLICIT_BLUEPRINTS.append((_bp, "/dashboard_customize"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.device_trust")
    _bp = getattr(_m, "device_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "device":
        EXPLICIT_BLUEPRINTS.append((_bp, "/device_trust"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.device_trust.blueprint")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "device_trust":
        EXPLICIT_BLUEPRINTS.append((_bp, "/blueprint"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.observability.diagnostics")
    _bp = getattr(_m, "diagnostics_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "diagnostics":
        EXPLICIT_BLUEPRINTS.append((_bp, "/diagnostics"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.feedback")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "feedback":
        EXPLICIT_BLUEPRINTS.append((_bp, "/feedback"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.finance")
    _bp = getattr(_m, "finance_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "finance":
        EXPLICIT_BLUEPRINTS.append((_bp, "/finance"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.finance")
    _bp = getattr(_m, "finance_api_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "finance_api":
        EXPLICIT_BLUEPRINTS.append((_bp, "/finance"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.health")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "health":
        EXPLICIT_BLUEPRINTS.append((_bp, "/health"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.health_checks")
    _bp = getattr(_m, "health_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "health_bp":
        EXPLICIT_BLUEPRINTS.append((_bp, "/health_checks"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.health_compat")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "health_compat":
        EXPLICIT_BLUEPRINTS.append((_bp, "/health_compat"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.help")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "help":
        EXPLICIT_BLUEPRINTS.append((_bp, "/help"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.hr")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "hr":
        EXPLICIT_BLUEPRINTS.append((_bp, "/hr"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.hr_workflows")
    _bp = getattr(_m, "hr_workflows_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "hr_workflows":
        EXPLICIT_BLUEPRINTS.append((_bp, "/hr_workflows"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.integration")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "integration":
        EXPLICIT_BLUEPRINTS.append((_bp, "/integration"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.api.integrations")
    _bp = getattr(_m, "integrations_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "integrations":
        EXPLICIT_BLUEPRINTS.append((_bp, "/integrations"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.inventory")
    _bp = getattr(_m, "inventory_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "inventory":
        EXPLICIT_BLUEPRINTS.append((_bp, "/inventory"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.inventory.routes_approval")
    _bp = getattr(_m, "inventory_approval_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "inventory_approval":
        EXPLICIT_BLUEPRINTS.append((_bp, "/routes_approval"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.inventory")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "inventory_bp":
        EXPLICIT_BLUEPRINTS.append((_bp, "/inventory"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.inventory.routes_delivery")
    _bp = getattr(_m, "inventory_delivery_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "inventory_delivery":
        EXPLICIT_BLUEPRINTS.append((_bp, "/routes_delivery"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.inventory.valuation")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "inventory_valuation":
        EXPLICIT_BLUEPRINTS.append((_bp, "/valuation"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.kanban")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "kanban":
        EXPLICIT_BLUEPRINTS.append((_bp, "/kanban"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.login_ui")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "login_ui":
        EXPLICIT_BLUEPRINTS.append((_bp, "/login_ui"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.main")
    _bp = getattr(_m, "main_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "main":
        EXPLICIT_BLUEPRINTS.append((_bp, "/main"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.manufacturing")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "manufacturing":
        EXPLICIT_BLUEPRINTS.append((_bp, "/manufacturing"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.marketing")
    _bp = getattr(_m, "marketing_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "marketing":
        EXPLICIT_BLUEPRINTS.append((_bp, "/marketing"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.metrics")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "metrics":
        EXPLICIT_BLUEPRINTS.append((_bp, "/metrics"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.auth.mfa_routes")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "mfa":
        EXPLICIT_BLUEPRINTS.append((_bp, "/mfa_routes"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.misc")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "misc":
        EXPLICIT_BLUEPRINTS.append((_bp, "/misc"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.ops.doctor")
    _bp = getattr(_m, "ops_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "ops":
        EXPLICIT_BLUEPRINTS.append((_bp, "/doctor"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.orders")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "orders":
        EXPLICIT_BLUEPRINTS.append((_bp, "/orders"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.plugins")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "plugins":
        EXPLICIT_BLUEPRINTS.append((_bp, "/plugins"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.plugins_sample")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "plugins_sample":
        EXPLICIT_BLUEPRINTS.append((_bp, "/plugins_sample"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.privacy")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "privacy":
        EXPLICIT_BLUEPRINTS.append((_bp, "/privacy"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.procurement")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "procurement":
        EXPLICIT_BLUEPRINTS.append((_bp, "/procurement"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.procurment.routes")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "procurment":
        EXPLICIT_BLUEPRINTS.append((_bp, "/routes"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.projects")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "projects":
        EXPLICIT_BLUEPRINTS.append((_bp, "/projects"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.recall")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "recall":
        EXPLICIT_BLUEPRINTS.append((_bp, "/recall"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.receive_inventory")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "receive_inventory":
        EXPLICIT_BLUEPRINTS.append((_bp, "/receive_inventory"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.report_builder")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "report_builder":
        EXPLICIT_BLUEPRINTS.append((_bp, "/report_builder"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.sales.routes")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "sales":
        EXPLICIT_BLUEPRINTS.append((_bp, "/routes"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.setup.opening_balances")
    _bp = getattr(_m, "setup_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "setup_opening":
        EXPLICIT_BLUEPRINTS.append((_bp, "/opening_balances"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.ops.status")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "status":
        EXPLICIT_BLUEPRINTS.append((_bp, "/status"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.supplychain.routes")
    _bp = getattr(_m, "supply_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "supplychain":
        EXPLICIT_BLUEPRINTS.append((_bp, "/routes"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.blueprints.telegram_webhook")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "telegram_webhook":
        EXPLICIT_BLUEPRINTS.append((_bp, "/telegram_webhook"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.tenders")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "tenders":
        EXPLICIT_BLUEPRINTS.append((_bp, "/tenders"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.web")
    _bp = getattr(_m, "web_bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "web":
        EXPLICIT_BLUEPRINTS.append((_bp, "/web"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
try:
    _m = import_module("erp.routes.webhooks")
    _bp = getattr(_m, "bp")
    # register only if it's really a Blueprint and names match the one we deduped by
    if isinstance(_bp, Blueprint) and _bp.name == "webhooks":
        EXPLICIT_BLUEPRINTS.append((_bp, "/webhooks"))
except Exception:
    # keep resilient: a bad import should not crash app creation in dev
    pass
