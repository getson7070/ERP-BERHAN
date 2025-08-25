from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    DateField,
    FloatField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired, Length, NumberRange
from datetime import datetime

from db import get_db
from erp.utils import hash_password, verify_password, login_required

bp = Blueprint('auth', __name__)


@bp.route('/choose_login', methods=['GET', 'POST'])
def choose_login():
    class ChooseLoginForm(FlaskForm):
        login_type = SelectField('Login Type', choices=[('employee', 'Employee'), ('client', 'Client')], validators=[DataRequired()])
        submit = SubmitField('Continue')
    form = ChooseLoginForm()
    if form.validate_on_submit():
        login_type = form.login_type.data
        if login_type == 'employee':
            return redirect(url_for('auth.employee_login'))
        elif login_type == 'client':
            return redirect(url_for('auth.client_login'))
    return render_template('choose_login.html', form=form)


@bp.route('/employee_login', methods=['GET', 'POST'])
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
            return redirect(url_for('main.dashboard'))
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


@bp.route('/client_login', methods=['GET', 'POST'])
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
            return redirect(url_for('main.dashboard'))
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


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.choose_login'))


@bp.route('/client_registration', methods=['GET', 'POST'])
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
    form.city.choices = [(c['city'], c['city']) for c in conn.execute('SELECT city FROM regions_cities WHERE region = ?', (form.region.data,)).fetchall()] if form.region.data else []
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
        return redirect(url_for('auth.choose_login'))
    conn.close()
    return render_template('client_registration.html', form=form)


@bp.route('/employee_registration', methods=['GET', 'POST'])
@login_required
def employee_registration():
    if 'user_management' not in session.get('permissions', []):
        return redirect(url_for('main.dashboard'))
    class EmployeeRegistrationForm(FlaskForm):
        username = StringField('Username (Phone Number)', validators=[DataRequired(), Length(min=10, max=10)])
        email = StringField('Email', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        role = SelectField('Role', choices=[('Sales Rep', 'Sales Rep'), ('Storekeeper', 'Storekeeper'), ('Accountant', 'Accountant'), ('Management', 'Management'), ('Cashier', 'Cashier'), ('Tender', 'Tender')], validators=[DataRequired()])
        permissions = SelectMultipleField('Permissions', validators=[DataRequired()])
        hire_date = DateField('Hire Date', validators=[DataRequired()])
        salary = FloatField('Salary (ETB)', validators=[DataRequired(), NumberRange(min=0)])
        submit = SubmitField('Register')
    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        permissions = form.permissions.data
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
        return redirect(url_for('main.dashboard'))
    return render_template('employee_registration.html', form=form)
