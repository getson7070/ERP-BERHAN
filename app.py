from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from blueprints import register_blueprints
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, IntegerField, FloatField, DateField, BooleanField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Length, NumberRange
from functools import wraps
import sqlite3
import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime
import csv
from io import TextIOWrapper
import os
import secrets

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("$argon2"):
        try:
            return ph.verify(password_hash, password)
        except VerifyMismatchError:
            return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(16))
register_blueprints(app)

def adapt_datetime(dt):
    return dt.isoformat(" ")
sqlite3.register_adapter(datetime, adapt_datetime)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('choose_login'))
        return f(*args, **kwargs)
    return wrap

def get_db():
    conn = sqlite3.connect('erp.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def log_access():
    if 'logged_in' in session and session['logged_in']:
        ip = request.remote_addr
        device = request.user_agent.string
        conn = get_db()
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn.execute('INSERT INTO access_logs (user, ip, device, timestamp) VALUES (?, ?, ?, ?)', (user, ip, device, datetime.now()))
        conn.commit()
        conn.close()

@app.route('/')
def index():
    return redirect(url_for('choose_login'))

@app.route('/choose_login', methods=['GET', 'POST'])
def choose_login():
    class ChooseLoginForm(FlaskForm):
        login_type = SelectField('Login Type', choices=[('employee', 'Employee'), ('client', 'Client')], validators=[DataRequired()])
        submit = SubmitField('Continue')
    form = ChooseLoginForm()
    if form.validate_on_submit():
        login_type = form.login_type.data
        if login_type == 'employee':
            return redirect(url_for('employee_login'))
        elif login_type == 'client':
            return redirect(url_for('client_login'))
    return render_template('choose_login.html', form=form)

@app.route('/employee_login', methods=['GET', 'POST'])
def employee_login():
    class LoginForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND user_type = ? AND approved_by_ceo = TRUE', (email, 'employee')).fetchone()
        if user and not user['account_locked'] and verify_password(password, user['password_hash']):
            session['logged_in'] = True
            session['role'] = 'employee'
            session['username'] = email
            session['permissions'] = user['permissions'].split(',') if user['permissions'] else []
            conn.execute('UPDATE users SET last_login = ?, failed_attempts = 0 WHERE email = ?', (datetime.now(), email))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            if user:
                if user['account_locked']:
                    flash('Account locked due to too many failed attempts.')
                else:
                    conn.execute('UPDATE users SET failed_attempts = failed_attempts + 1 WHERE email = ?', (email,))
                    attempts = user['failed_attempts'] + 1
                    if attempts >= 5:
                        conn.execute('UPDATE users SET account_locked = TRUE WHERE email = ?', (email,))
                        flash('Account locked due to too many failed attempts.')
                    else:
                        flash('Invalid email/password or not approved.')
                    conn.commit()
            else:
                flash('Invalid email/password or not approved.')
            conn.close()
    return render_template('employee_login.html', form=form)

@app.route('/client_login', methods=['GET', 'POST'])
def client_login():
    class LoginForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND user_type = ? AND approved_by_ceo = TRUE', (email, 'client')).fetchone()
        if user and not user['account_locked'] and verify_password(password, user['password_hash']):
            session['logged_in'] = True
            session['role'] = 'client'
            session['tin'] = user['tin']
            session['username'] = email
            session['permissions'] = user['permissions'].split(',') if user['permissions'] else []
            conn.execute('UPDATE users SET last_login = ?, failed_attempts = 0 WHERE email = ?', (datetime.now(), email))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            if user:
                if user['account_locked']:
                    flash('Account locked due to too many failed attempts.')
                else:
                    conn.execute('UPDATE users SET failed_attempts = failed_attempts + 1 WHERE email = ?', (email,))
                    attempts = user['failed_attempts'] + 1
                    if attempts >= 5:
                        conn.execute('UPDATE users SET account_locked = TRUE WHERE email = ?', (email,))
                        flash('Account locked due to too many failed attempts.')
                    else:
                        flash('Invalid email/password or not approved.')
                    conn.commit()
            else:
                flash('Invalid email/password or not approved.')
            conn.close()
    return render_template('client_login.html', form=form)

@app.route('/client_registration', methods=['GET', 'POST'])
def client_registration():
    class ClientRegistrationForm(FlaskForm):
        tin = StringField('TIN', validators=[DataRequired(), Length(min=10, max=10)])
        institution_name = StringField('Institution Name', validators=[DataRequired()])
        address = StringField('Address', validators=[DataRequired()])
        phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=10)])
        region = SelectField('Region', validators=[DataRequired()])
        city = SelectField('City', validators=[DataRequired()])
        email = StringField('Email', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Register')
    conn = get_db()
    form = ClientRegistrationForm()
    form.region.choices = [(r['region'], r['region']) for r in conn.execute('SELECT DISTINCT region FROM regions_cities').fetchall()]
    if not form.region.data and form.region.choices:
        form.region.data = form.region.choices[0][0]
    form.city.choices = [
        (c['city'], c['city'])
        for c in conn.execute('SELECT city FROM regions_cities WHERE region = ?', (form.region.data,)).fetchall()
    ] if form.region.data else []
    if form.validate_on_submit():
        tin = form.tin.data
        if not tin.isdigit():
            flash('TIN must be a 10-digit number.')
            conn.close()
            return render_template('client_registration.html', form=form)
        institution_name = form.institution_name.data
        address = form.address.data
        phone = form.phone.data
        if not (phone.startswith(('09', '07')) and phone.isdigit()):
            flash('Phone must be a 10-digit number starting with 09 or 07.')
            conn.close()
            return render_template('client_registration.html', form=form)
        region = form.region.data
        city = form.city.data
        email = form.email.data
        password = form.password.data
        if conn.execute('SELECT * FROM users WHERE tin = ? OR email = ?', (tin, email)).fetchone():
            flash('TIN or email already registered.')
            conn.close()
            return render_template('client_registration.html', form=form)
        password_hash = hash_password(password)
        conn.execute('''
            INSERT INTO users (user_type, tin, institution_name, address, phone, region, city, email, password_hash, permissions, approved_by_ceo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('client', tin, institution_name, address, phone, region, city, email, password_hash, 'put_order,my_orders,order_status,maintenance_request,maintenance_status,message', False))
        conn.commit()
        conn.close()
        return redirect(url_for('choose_login'))
    conn.close()
    return render_template('client_registration.html', form=form)

@app.route('/employee_registration', methods=['GET', 'POST'])
@login_required
def employee_registration():
    if 'user_management' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class EmployeeRegistrationForm(FlaskForm):
        username = StringField('Username (Phone Number)', validators=[DataRequired(), Length(min=10, max=10)])
        email = StringField('Email', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        role = SelectField('Role', choices=[('Sales Rep', 'Sales Rep'), ('Storekeeper', 'Storekeeper'), ('Accountant', 'Accountant'), ('Management', 'Management'), ('Cashier', 'Cashier'), ('Tender', 'Tender')], validators=[DataRequired()])
        permissions = SelectMultipleField('Permissions', choices=[
            ('add_report', 'Add Report'), ('my_report', 'My Report'), ('marketing_report', 'Marketing Report'),
            ('add_inventory', 'Add Inventory'), ('receive_inventory', 'Receive Inventory'), ('inventory_out', 'Inventory Out'),
            ('inventory_report', 'Inventory Report'), ('add_tender', 'Add Tender'), ('tenders_list', 'Tenders List'),
            ('tenders_report', 'Tenders Report'), ('view_orders', 'View Orders'), ('put_order', 'Put Order'),
            ('maintenance_request', 'Maintenance Request'), ('maintenance_status', 'Maintenance Status'),
            ('maintenance_followup', 'Maintenance Followup'), ('maintenance_report', 'Maintenance Report'),
            ('user_management', 'User Management')
        ], validators=[DataRequired()])
        hire_date = DateField('Hire Date', validators=[DataRequired()])
        salary = FloatField('Salary (ETB)', validators=[DataRequired(), NumberRange(min=0)])
        submit = SubmitField('Register')
    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        permissions = ','.join(form.permissions.data)
        hire_date = form.hire_date.data
        salary = form.salary.data
        conn = get_db()
        if conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone():
            flash('Username or email already registered.')
            conn.close()
            return render_template('employee_registration.html', form=form)
        password_hash = hash_password(password)
        conn.execute('''
            INSERT INTO users (user_type, username, email, password_hash, permissions, approved_by_ceo, hire_date, salary, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('employee', username, email, password_hash, permissions, False, hire_date, salary, role))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('employee_registration.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('analytics.dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('choose_login'))

@app.route('/user_management', methods=['GET', 'POST'])
@login_required
def user_management():
    if 'user_management' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class UserManagementForm(FlaskForm):
        username = StringField('Username/TIN', validators=[DataRequired()])
        action = SelectField('Action', choices=[('approve', 'Approve'), ('reject', 'Reject')], validators=[DataRequired()])
        submit = SubmitField('Submit')
    form = UserManagementForm()
    conn = get_db()
    if form.validate_on_submit():
        username = form.username.data
        action = form.action.data
        if action == 'approve':
            conn.execute('UPDATE users SET approved_by_ceo = TRUE WHERE username = ? OR tin = ?', (username, username))
        elif action == 'reject':
            conn.execute('DELETE FROM users WHERE username = ? OR tin = ?', (username, username))
        conn.commit()
    users = conn.execute('SELECT * FROM users WHERE approved_by_ceo = FALSE').fetchall()
    conn.close()
    return render_template('user_management.html', form=form, users=users)

@app.route('/upload_institutions', methods=['GET', 'POST'])
@login_required
def upload_institutions():
    if 'user_management' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class UploadForm(FlaskForm):
        file = FileField('CSV File', validators=[DataRequired()])
        submit = SubmitField('Upload')
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and file.filename.endswith('.csv'):
            csv_file = TextIOWrapper(file, encoding='utf-8')
            reader = csv.DictReader(csv_file)
            conn = get_db()
            for row in reader:
                if 'tin' in row and 'institution_name' in row:
                    conn.execute('INSERT OR IGNORE INTO users (user_type, tin, institution_name, approved_by_ceo) VALUES (?, ?, ?, ?)',
                                ('client', row['tin'], row['institution_name'], False))
            conn.commit()
            conn.close()
            flash('Institutions uploaded for approval.')
            return redirect(url_for('user_management'))
        flash('Invalid CSV file.')
    return render_template('upload_institutions.html', form=form)

@app.route('/add_report', methods=['GET', 'POST'])
@login_required
def add_report():
    if 'add_report' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class ReportForm(FlaskForm):
        institution = SelectField('Institution', validators=[DataRequired()])
        new_institution = StringField('New Institution')
        region = SelectField('Region', validators=[DataRequired()])
        city = SelectField('City', validators=[DataRequired()])
        location_detail = StringField('Location Detail')
        phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=10)])
        visit_date = DateField('Visit Date', validators=[DataRequired()])
        products = SelectMultipleField('Products', validators=[DataRequired()])
        other_detail = StringField('Other Product Details')
        outcome = SelectField('Outcome', choices=[('Sale', 'Sale'), ('Contract', 'Contract'), ('Negotiation', 'Negotiation'), ('No Interest', 'No Interest')], default='Sale', validators=[DataRequired()])
        sale_amount = FloatField('Sale Amount (ETB)', validators=[NumberRange(min=0)])
        visit_type = SelectField('Visit Type', choices=[('First Visit', 'First Visit'), ('Follow-up', 'Follow-up')], validators=[DataRequired()])
        follow_up = StringField('Follow-up Details')
        submit = SubmitField('Submit')
    conn = get_db()
    form = ReportForm()
    institutions = [row['institution_name'] for row in conn.execute('SELECT DISTINCT institution_name FROM users WHERE institution_name IS NOT NULL').fetchall()]
    form.institution.choices = [(i, i) for i in institutions] + [('new', 'New')]
    form.region.choices = [(r['region'], r['region']) for r in conn.execute('SELECT DISTINCT region FROM regions_cities').fetchall()]
    form.city.choices = [(c['city'], c['city']) for c in conn.execute('SELECT city FROM regions_cities WHERE region = ?', (form.region.data,)).fetchall()] if form.region.data else []
    form.products.choices = [
        ('EXI1800', 'CLIA: EXI1800'), ('EXI1820', 'CLIA: EXI1820'), ('EXI2400', 'CLIA: EXI2400'),
        ('EXC200', 'Chemistry: EXC200'), ('EXC420', 'Chemistry: EXC420'),
        ('EXR110', 'POCT: EXR110'), ('EXR120', 'POCT: EXR120'), ('Q8 PRO', 'POCT: Q8 PRO'),
        ('EXC8000', 'Hematology: EXC8000'), ('EXC6000', 'Hematology: EXC6000'), ('Z50', 'Hematology: Z50'), ('Z3', 'Hematology: Z3'), ('Z3 CRP', 'Hematology: Z3 CRP'),
        ('EXS2600', 'Microbiology: EXS2600'), ('EXB120', 'Microbiology: EXB120'),
        ('DW-350', 'Ultrasound: DW-350'), ('DW-360', 'Ultrasound: DW-360'), ('DW-370', 'Ultrasound: DW-370'), ('DW-580', 'Ultrasound: DW-580'),
        ('DW-CE540', 'Ultrasound: DW-CE540'), ('DW-CE780', 'Ultrasound: DW-CE780'), ('DW-CT520', 'Ultrasound: DW-CT520'),
        ('DW-PE522', 'Ultrasound: DW-PE522'), ('DW-PE542', 'Ultrasound: DW-PE542'), ('DW-PE512', 'Ultrasound: DW-PE512'),
        ('OTHERS', 'Other: OTHERS')
    ]
    if form.validate_on_submit():
        institution = form.institution.data if form.institution.data != 'new' else form.new_institution.data
        if form.institution.data == 'new':
            flash('New institution added for approval.')
        region = form.region.data
        city = form.city.data
        location_detail = form.location_detail.data
        phone = form.phone.data
        if not (phone.startswith(('09', '07')) and phone.isdigit()):
            flash('Phone must be a 10-digit number starting with 09 or 07.')
            conn.close()
            return render_template('add_report.html', form=form)
        visit_date = form.visit_date.data
        products = form.products.data
        other_detail = form.other_detail.data if 'OTHERS' in products else ''
        outcome = form.outcome.data
        sale_amount = form.sale_amount.data if outcome == 'Sale' else None
        visit_type = form.visit_type.data
        follow_up = form.follow_up.data if visit_type == 'Follow-up' else None
        location = f"{region}, {city}, {location_detail}" if city and location_detail else f"{region}, {location_detail}"
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn.execute('''
            INSERT INTO reports (institution, location, owner, phone, visit_date, interested_products, outcome, sale_amount, visit_type, follow_up_details, sales_rep)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (institution, location, '', phone, visit_date, ', '.join(products), outcome, sale_amount, visit_type, follow_up, user))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('add_report.html', form=form)

@app.route('/get_cities')
def get_cities():
    region = request.args.get('region')
    conn = get_db()
    cities = [row['city'] for row in conn.execute('SELECT city FROM regions_cities WHERE region = ?', (region,)).fetchall()]
    conn.close()
    return jsonify(cities=cities)

@app.route('/my_report')
@login_required
def my_report():
    if 'my_report' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    user = session['username'] if session['role'] == 'employee' else session['tin']
    reports = conn.execute('SELECT * FROM reports WHERE sales_rep = ? ORDER BY visit_date DESC LIMIT 5', (user,)).fetchall()
    conn.close()
    return render_template('my_report.html', reports=reports)

@app.route('/promotion_report_sales')
@login_required
def promotion_report_sales():
    if 'marketing_report' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    reports = conn.execute('SELECT * FROM reports WHERE outcome IN ("Sale", "Contract", "Negotiation") ORDER BY visit_date DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('promotion_report_sales.html', reports=reports)

@app.route('/promotion_report_activities')
@login_required
def promotion_report_activities():
    if 'marketing_report' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    reports = conn.execute('SELECT * FROM reports WHERE outcome = "No Interest" ORDER BY visit_date DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('promotion_report_activities.html', reports=reports)

@app.route('/put_order', methods=['GET', 'POST'])
@login_required
def put_order():
    if 'put_order' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class OrderForm(FlaskForm):
        item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
        quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
        customer = StringField('Customer', validators=[DataRequired()])
        vat_exempt = BooleanField('VAT Exempt')
        submit = SubmitField('Submit Order')
    conn = get_db()
    form = OrderForm()
    form.item_id.choices = [(item['id'], item['item_code']) for item in conn.execute('SELECT id, item_code FROM inventory').fetchall()]
    if form.validate_on_submit():
        item_id = form.item_id.data
        quantity = form.quantity.data
        customer = form.customer.data
        vat_exempt = form.vat_exempt.data
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn.execute('''
            INSERT INTO orders (item_id, quantity, customer, sales_rep, vat_exempt, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (item_id, quantity, customer, user, vat_exempt))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('put_order.html', form=form)

@app.route('/approve_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def approve_order(order_id):
    if 'view_orders' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class ApproveOrderForm(FlaskForm):
        submit = SubmitField('Approve')
    form = ApproveOrderForm()
    conn = get_db()
    if form.validate_on_submit():
        conn.execute('UPDATE orders SET status = "approved" WHERE id = ?', (order_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('orders'))
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    return render_template('approve_order.html', form=form, order=order)

@app.route('/amend_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def amend_order(order_id):
    if 'view_orders' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class AmendOrderForm(FlaskForm):
        item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
        quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
        customer = StringField('Customer', validators=[DataRequired()])
        vat_exempt = BooleanField('VAT Exempt')
        submit = SubmitField('Amend')
    conn = get_db()
    form = AmendOrderForm()
    form.item_id.choices = [(item['id'], item['item_code']) for item in conn.execute('SELECT id, item_code FROM inventory').fetchall()]
    if form.validate_on_submit():
        item_id = form.item_id.data
        quantity = form.quantity.data
        customer = form.customer.data
        vat_exempt = form.vat_exempt.data
        conn.execute('UPDATE orders SET item_id = ?, quantity = ?, customer = ?, vat_exempt = ?, status = "pending" WHERE id = ?', (item_id, quantity, customer, vat_exempt, order_id))
        conn.commit()
        conn.close()
        return redirect(url_for('orders'))
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if order:
        form.item_id.data = order['item_id']
        form.quantity.data = order['quantity']
        form.customer.data = order['customer']
        form.vat_exempt.data = order['vat_exempt']
    conn.close()
    return render_template('amend_order.html', form=form, order=order)

@app.route('/reject_order/<int:order_id>')
@login_required
def reject_order(order_id):
    if 'view_orders' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    conn.execute('UPDATE orders SET status = "rejected" WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('orders'))

@app.route('/my_orders')
@login_required
def my_orders():
    if 'my_orders' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    user = session['username'] if session['role'] == 'employee' else session['tin']
    orders = conn.execute('SELECT * FROM orders WHERE sales_rep = ? OR customer = ? ORDER BY id DESC LIMIT 5', (user, user)).fetchall()
    conn.close()
    return render_template('my_orders.html', orders=orders)

@app.route('/add_inventory', methods=['GET', 'POST'])
@login_required
def add_inventory():
    if 'add_inventory' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class InventoryForm(FlaskForm):
        description = StringField('Description', validators=[DataRequired()])
        pack_size = SelectField('Pack Size', validators=[DataRequired()])
        brand = StringField('Brand', validators=[DataRequired()])
        type = SelectField('Type', choices=[('Device', 'Device'), ('Reagent', 'Reagent')], validators=[DataRequired()])
        exp_date = DateField('Expiration Date')
        category = StringField('Category', validators=[DataRequired()])
        submit = SubmitField('Submit')
    conn = get_db()
    form = InventoryForm()
    form.pack_size.choices = [(p['pack_size'], p['pack_size']) for p in conn.execute('SELECT DISTINCT pack_size FROM pack_sizes').fetchall()]
    if form.validate_on_submit():
        description = form.description.data
        pack_size = form.pack_size.data
        brand = form.brand.data
        type_ = form.type.data
        exp_date = form.exp_date.data if type_ == 'Reagent' else None
        category = form.category.data
        initials = ''.join(word[0].upper() for word in brand.split())
        seq = conn.execute('SELECT COUNT(*) FROM inventory').fetchone()[0] + 1
        item_code = f"{category[:3].upper()}-{initials}-{pack_size}-{seq:04d}"
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn.execute('''
            INSERT INTO inventory (item_code, description, pack_size, brand, type, exp_date, category, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item_code, description, pack_size, brand, type_, exp_date, category, 0))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('add_inventory.html', form=form)

@app.route('/add_supplier', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if 'add_inventory' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class SupplierForm(FlaskForm):
        name = StringField('Supplier Name', validators=[DataRequired()])
        brands = TextAreaField('Brands (comma-separated)', validators=[DataRequired()])
        submit = SubmitField('Submit')
    form = SupplierForm()
    if form.validate_on_submit():
        name = form.name.data
        brands = form.brands.data.split(',')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO suppliers (name) VALUES (?)', (name,))
        supplier_id = cursor.lastrowid
        for brand in brands:
            cursor.execute('INSERT INTO supplier_brands (supplier_id, brand) VALUES (?, ?)', (supplier_id, brand.strip()))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('add_supplier.html', form=form)

@app.route('/add_pack_size', methods=['GET', 'POST'])
@login_required
def add_pack_size():
    if 'add_inventory' in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class PackSizeForm(FlaskForm):
        pack_size = StringField('Pack Size', validators=[DataRequired()])
        submit = SubmitField('Submit')
    form = PackSizeForm()
    if form.validate_on_submit():
        pack_size = form.pack_size.data
        conn = get_db()
        conn.execute('INSERT INTO pack_sizes (pack_size) VALUES (?)', (pack_size,))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('add_pack_size.html', form=form)

@app.route('/receive_inventory', methods=['GET', 'POST'])
@login_required
def receive_inventory():
    if 'receive_inventory' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class ReceiveForm(FlaskForm):
        item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
        quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
        submit = SubmitField('Submit')
    conn = get_db()
    form = ReceiveForm()
    form.item_id.choices = [(item['id'], item['item_code']) for item in conn.execute('SELECT id, item_code FROM inventory').fetchall()]
    if form.validate_on_submit():
        item_id = form.item_id.data
        quantity = form.quantity.data
        conn.execute('UPDATE inventory SET stock = stock + ? WHERE id = ?', (quantity, item_id))
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn.execute('INSERT INTO inventory_movements (item_id, quantity, action, date, user) VALUES (?, ?, "Receive", ?, ?)', (item_id, quantity, datetime.now(), user))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('receive_inventory.html', form=form)

@app.route('/inventory_out', methods=['GET', 'POST'])
@login_required
def inventory_out():
    if 'inventory_out' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class InventoryOutForm(FlaskForm):
        order_id = SelectField('Approved Order', coerce=int, validators=[DataRequired()])
        quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
        action = SelectField('Action', choices=[('Sales', 'Sales'), ('Delivery', 'Delivery')], validators=[DataRequired()])
        sub_action = SelectField('Sub-Action', validators=[DataRequired()])
        submit = SubmitField('Submit')
    conn = get_db()
    form = InventoryOutForm()
    form.order_id.choices = [(o['id'], f"ID: {o['id']}, Item ID: {o['item_id']}, Qty: {o['quantity']}, Customer: {o['customer']}") for o in conn.execute('SELECT * FROM orders WHERE status = "approved"').fetchall()]
    if form.validate_on_submit():
        order_id = form.order_id.data
        quantity = form.quantity.data
        action = form.action.data
        sub_action = form.sub_action.data
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        stock = conn.execute('SELECT stock FROM inventory WHERE id = ?', (order['item_id'],)).fetchone()['stock']
        if stock < quantity:
            flash('Insufficient stock.')
            conn.close()
            return render_template('inventory_out.html', form=form)
        conn.execute('UPDATE inventory SET stock = stock - ? WHERE id = ?', (quantity, order['item_id']))
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn.execute('INSERT INTO inventory_movements (item_id, quantity, action, sub_action, date, user, order_id) VALUES (?, ?, ?, ?, ?, ?, ?)', (order['item_id'], quantity, action, sub_action, datetime.now(), user, order_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('inventory_out.html', form=form)

@app.route('/add_tender', methods=['GET', 'POST'])
@login_required
def add_tender():
    if 'add_tender' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class TenderForm(FlaskForm):
        tender_type_id = SelectField('Tender Type', coerce=int, validators=[DataRequired()])
        description = StringField('Description', validators=[DataRequired()])
        due_date = DateField('Due Date', validators=[DataRequired()])
        institution = StringField('Institution')
        envelope_type = SelectField('Envelope Type', choices=[('One Envelope', 'One Envelope'), ('Two Envelope', 'Two Envelope')], validators=[DataRequired()])
        private_key = StringField('Private Key')
        tech_key = StringField('Technical Key')
        fin_key = StringField('Financial Key')
        submit = SubmitField('Submit')
    conn = get_db()
    form = TenderForm()
    form.tender_type_id.choices = [(t['id'], t['type_name']) for t in conn.execute('SELECT id, type_name FROM tender_types').fetchall()]
    if form.validate_on_submit():
        tender_type_id = form.tender_type_id.data
        description = form.description.data
        due_date = form.due_date.data
        institution = form.institution.data
        envelope_type = form.envelope_type.data
        private_key = form.private_key.data if envelope_type == 'One Envelope' else None
        tech_key = form.tech_key.data if envelope_type == 'Two Envelope' else None
        fin_key = form.fin_key.data if envelope_type == 'Two Envelope' else None
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn.execute('''
            INSERT INTO tenders (tender_type_id, description, due_date, status, user, institution, envelope_type, private_key, tech_key, fin_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tender_type_id, description, due_date, 'Open', user, institution, envelope_type, private_key, tech_key, fin_key))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('add_tender.html', form=form)

@app.route('/tenders_list')
@login_required
def tenders_list():
    if 'tenders_list' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    tenders = conn.execute('SELECT t.id, tt.type_name, t.description, t.due_date, t.status, t.user, t.institution, t.envelope_type FROM tenders t JOIN tender_types tt ON t.tender_type_id = tt.id ORDER BY t.due_date ASC LIMIT 5').fetchall()
    conn.close()
    return render_template('tenders_list.html', tenders=tenders)

@app.route('/tenders_report')
@login_required
def tenders_report():
    if 'tenders_report' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    tenders = conn.execute('SELECT t.id, tt.type_name, t.description, t.due_date, t.status, t.user, t.institution, t.envelope_type FROM tenders t JOIN tender_types tt ON t.tender_type_id = tt.id ORDER BY t.due_date ASC LIMIT 5').fetchall()
    conn.close()
    return render_template('tenders_report.html', tenders=tenders)

@app.route('/orders')
@login_required
def orders():
    if 'view_orders' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    pending_orders = conn.execute('SELECT * FROM orders WHERE status = "pending" ORDER BY id DESC LIMIT 5').fetchall()
    approved_orders = conn.execute('SELECT * FROM orders WHERE status = "approved" ORDER BY id DESC LIMIT 5').fetchall()
    rejected_orders = conn.execute('SELECT * FROM orders WHERE status = "rejected" ORDER BY id DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('orders.html', pending_orders=pending_orders, approved_orders=approved_orders, rejected_orders=rejected_orders)

@app.route('/maintenance_request', methods=['GET', 'POST'])
@login_required
def maintenance_request():
    if 'maintenance_request' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class MaintenanceForm(FlaskForm):
        equipment_id = IntegerField('Equipment ID', validators=[DataRequired()])
        type = StringField('Type', validators=[DataRequired()])
        submit = SubmitField('Submit Request')
    form = MaintenanceForm()
    if form.validate_on_submit():
        equipment_id = form.equipment_id.data
        type_ = form.type.data
        user = session['username'] if session['role'] == 'employee' else session['tin']
        conn = get_db()
        conn.execute('INSERT INTO maintenance (equipment_id, request_date, type, status, user) VALUES (?, ?, ?, ?, ?)', (equipment_id, datetime.now(), type_, 'pending', user))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('maintenance_request.html', form=form)

@app.route('/maintenance_status')
@login_required
def maintenance_status():
    if 'maintenance_status' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    user = session['username'] if session['role'] == 'employee' else session['tin']
    maintenance = conn.execute('SELECT * FROM maintenance WHERE user = ? ORDER BY request_date DESC LIMIT 5', (user,)).fetchall()
    conn.close()
    return render_template('maintenance_status.html', maintenance=maintenance)

@app.route('/maintenance_followup', methods=['GET', 'POST'])
@login_required
def maintenance_followup():
    if 'maintenance_followup' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    class MaintenanceFollowupForm(FlaskForm):
        maintenance_id = SelectField('Maintenance ID', coerce=int, validators=[DataRequired()])
        report = TextAreaField('Report Details', validators=[DataRequired()])
        action = SelectField('Action', choices=[('approve', 'Approve'), ('reject', 'Reject')], validators=[DataRequired()])
        submit = SubmitField('Submit')
    conn = get_db()
    form = MaintenanceFollowupForm()
    form.maintenance_id.choices = [(m['id'], f"ID: {m['id']}, Equipment: {m['equipment_id']}") for m in conn.execute('SELECT * FROM maintenance WHERE status = "pending"').fetchall()]
    if form.validate_on_submit():
        maintenance_id = form.maintenance_id.data
        report = form.report.data
        action = form.action.data
        user = session['username'] if session['role'] == 'employee' else session['tin']
        status = 'approved' if action == 'approve' else 'rejected'
        conn.execute('UPDATE maintenance SET status = ?, report = ?, user = ? WHERE id = ?', (status, report, user, maintenance_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('maintenance_followup.html', form=form)

@app.route('/maintenance_report')
@login_required
def maintenance_report():
    if 'maintenance_report' not in session.get('permissions', []):
        return redirect(url_for('dashboard'))
    conn = get_db()
    maintenance = conn.execute('SELECT * FROM maintenance ORDER BY request_date DESC LIMIT 10').fetchall()
    conn.close()
    return render_template('maintenance_report.html', maintenance=maintenance)

@app.route('/message', methods=['GET', 'POST'])
@login_required
def message():
    class MessageForm(FlaskForm):
        message = TextAreaField('Message', validators=[DataRequired()])
        submit = SubmitField('Send')
    form = MessageForm()
    if form.validate_on_submit():
        message = form.message.data
        conn = get_db()
        user = session['tin']
        conn.execute('INSERT INTO messages (tin, message, date) VALUES (?, ?, ?)', (user, message, datetime.now()))
        conn.commit()
        conn.close()
        flash('Message sent to support.')
        return redirect(url_for('dashboard'))
    return render_template('message.html', form=form)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)