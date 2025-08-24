        diff --git a/app.py b/app.py
index 037e7b6e84322bda39c1226cb0b599e8fc85e48d..d2c8bdde12db005ca3ebdf649c15a7bc15e321c3 100644
--- a/app.py
+++ b/app.py
@@ -1,38 +1,40 @@
-from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
+from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
+from blueprints import register_blueprints
 from flask_wtf import FlaskForm
 from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, IntegerField, FloatField, DateField, BooleanField, SelectMultipleField, FileField
 from wtforms.validators import DataRequired, Length, NumberRange
 from functools import wraps
 import sqlite3
 import bcrypt
 from datetime import datetime
 import csv
 from io import TextIOWrapper
 
-app = Flask(__name__)
-app.secret_key = 'your_secret_key'  # Replace with a secure key
+app = Flask(__name__)
+app.secret_key = 'your_secret_key'  # Replace with a secure key
+register_blueprints(app)
 
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
diff --git a/app.py b/app.py
index 037e7b6e84322bda39c1226cb0b599e8fc85e48d..d2c8bdde12db005ca3ebdf649c15a7bc15e321c3 100644
--- a/app.py
+++ b/app.py
@@ -185,58 +187,54 @@ def employee_registration():
         submit = SubmitField('Register')
     form = EmployeeRegistrationForm()
     if form.validate_on_submit():
         username = form.username.data
         email = form.email.data
         password = form.password.data.encode('utf-8')
         role = form.role.data
         permissions = ','.join(form.permissions.data)
         hire_date = form.hire_date.data
         salary = form.salary.data
         conn = get_db()
         if conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone():
             flash('Username or email already registered.')
             conn.close()
             return render_template('employee_registration.html', form=form)
         password_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
         conn.execute('''
             INSERT INTO users (user_type, username, email, password_hash, permissions, approved_by_ceo, hire_date, salary, role)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
         ''', ('employee', username, email, password_hash, permissions, False, hire_date, salary, role))
         conn.commit()
         conn.close()
         return redirect(url_for('dashboard'))
     return render_template('employee_registration.html', form=form)
 
-@app.route('/dashboard')
-@login_required
-def dashboard():
-    conn = get_db()
-    pending_orders = conn.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"').fetchone()[0]
-    pending_maintenance = conn.execute('SELECT COUNT(*) FROM maintenance WHERE status = "pending"').fetchone()[0]
-    conn.close()
-    return render_template('dashboard.html', role=session.get('role'), permissions=session.get('permissions', []), pending_orders=pending_orders, pending_maintenance=pending_maintenance)
+@app.route('/dashboard')
+@login_required
+def dashboard():
+    return redirect(url_for('analytics.dashboard'))
 
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
