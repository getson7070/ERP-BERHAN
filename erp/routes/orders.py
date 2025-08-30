from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime

from sqlalchemy import text
from db import get_db
from erp.utils import login_required, has_permission, idempotency_key_required

bp = Blueprint('orders', __name__)


@bp.route('/put_order', methods=['GET', 'POST'])
@login_required
@idempotency_key_required
def put_order():
    if not has_permission('put_order'):
        return redirect(url_for('main.dashboard'))
    class OrderForm(FlaskForm):
        item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
        quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
        customer = StringField('Customer', validators=[DataRequired()])
        vat_exempt = BooleanField('VAT Exempt')
        submit = SubmitField('Submit Order')
    conn = get_db()
    cur = conn.execute(text('SELECT id, item_code FROM inventory'))
    form = OrderForm()
    form.item_id.choices = [(row[0], row[1]) for row in cur.fetchall()]
    if form.validate_on_submit():
        item_id = form.item_id.data
        quantity = form.quantity.data
        customer = form.customer.data
        vat_exempt = form.vat_exempt.data
        user = session.get('username') if session.get('role') != 'Client' else session['tin']
        conn.execute(
            text(
                "INSERT INTO orders (item_id, quantity, customer, sales_rep, vat_exempt, status) "
                "VALUES (:item_id, :quantity, :customer, :sales_rep, :vat_exempt, 'pending')"
            ),
            {
                'item_id': item_id,
                'quantity': quantity,
                'customer': customer,
                'sales_rep': user,
                'vat_exempt': vat_exempt,
            },
        )
        conn.commit()
        conn.close()
        return redirect(url_for('main.dashboard'))
    conn.close()
    return render_template('put_order.html', form=form)


@bp.route('/orders')
@login_required
def orders():
    if not has_permission('view_orders'):
        return redirect(url_for('main.dashboard'))
    conn = get_db()
    pending_orders = conn.execute(
        text("SELECT * FROM orders WHERE status = 'pending' ORDER BY id DESC LIMIT 5")
    ).fetchall()
    approved_orders = conn.execute(
        text("SELECT * FROM orders WHERE status = 'approved' ORDER BY id DESC LIMIT 5")
    ).fetchall()
    rejected_orders = conn.execute(
        text("SELECT * FROM orders WHERE status = 'rejected' ORDER BY id DESC LIMIT 5")
    ).fetchall()
    conn.close()
    return render_template('orders.html', pending_orders=pending_orders, approved_orders=approved_orders, rejected_orders=rejected_orders)
