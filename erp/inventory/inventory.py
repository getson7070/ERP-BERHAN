from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..extensions import db
from ..models import Item
from ..forms import ItemForm

inventory_bp = Blueprint("inventory", __name__, template_folder="../templates/inventory")

@inventory_bp.get("/")
@login_required
def index():
    items = Item.query.order_by(Item.id.desc()).limit(100).all()
    return render_template("inventory/index.html", items=items)

@inventory_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_item():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            sku=form.sku.data.strip(),
            name=form.name.data.strip(),
            qty_on_hand=form.qty_on_hand.data or 0,
            price=form.price.data or 0,
        )
        db.session.add(item)
        db.session.commit()
        flash("Item created.", "success")
        return redirect(url_for("inventory.index"))
    return render_template("inventory/new.html", form=form)
