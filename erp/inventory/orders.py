﻿from __future__ import annotations
from flask import Blueprint, render_template
from flask_login import login_required
from ..models import Order

orders_bp = Blueprint("orders", __name__, template_folder="../templates/orders")

@orders_bp.get("/")
@login_required
def index():
    orders = Order.query.order_by(Order.id.desc()).limit(100).all()
    return render_template("orders/index.html", orders=orders)


