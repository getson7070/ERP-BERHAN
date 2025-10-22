﻿from __future__ import annotations
from flask import Blueprint, jsonify

# Phase-1 health endpoints
health_bp = Blueprint("health", __name__)

@health_bp.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200

@health_bp.get("/readyz")
def readyz():
    # Keep simple for local boot; extend as needed.
    return jsonify(status="ready"), 200
