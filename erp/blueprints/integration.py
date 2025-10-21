﻿from flask import Blueprint, jsonify, request
from erp.extensions import db
from erp.models.integration import IntegrationConfig

integration_bp = Blueprint("integration", __name__, url_prefix="/integration")

@integration_bp.get("/health")
def health():
    return jsonify(ok=True, module="integration")

@integration_bp.get("/configs")
def list_configs():
    rows = IntegrationConfig.query.order_by(IntegrationConfig.created_at.desc()).all()
    return jsonify([{
        "id": r.id, "name": r.name, "provider": r.provider,
        "enabled": r.enabled, "config_json": r.config_json
    } for r in rows])

@integration_bp.post("/configs")
def upsert_config():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify(error="name_required"), 400
    row = IntegrationConfig.query.filter_by(name=name).one_or_none()
    if row is None:
        row = IntegrationConfig(name=name, provider=data.get("provider","custom"))
        db.session.add(row)
    row.enabled = bool(data.get("enabled", True))
    row.config_json = data.get("config_json", {})
    db.session.commit()
    return jsonify(id=row.id, name=row.name)


