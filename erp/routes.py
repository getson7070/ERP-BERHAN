from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db  # Relative from erp/
from ..models.user import User  # Assume models.user
from .forms import LoginForm, ForgotPasswordForm  # From erp/forms.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import abort

# Global limiter (init in factory or here)
limiter = Limiter(key_func=get_remote_address)

# Auth Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='../templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            # TODO: Send email via Flask-Mail
            flash('Reset link sent to your email.', 'info')
        else:
            flash('Email not found.', 'error')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot.html', form=form)  # Create forgot.html if needed

# MFA stub (expand as needed)
@auth_bp.route('/mfa/start')
@login_required
def mfa_start():
    if not current_user.mfa_enabled:  # Assume model attr
        flash('MFA not enabled. Enable in profile.', 'warning')
        return redirect(url_for('profile.edit'))
    return render_template('mfa/start.html')  # Create template

# Main registration function (for erp/__init__.py create_app)
def register_blueprints(app):
    from .inventory.routes import inventory_bp
    from .crm.routes import crm_bp
    # ... other blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(crm_bp)
    # Add more as per your modules

# Example main blueprint (if not separate)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

# Register main too
def register_main(app):
    app.register_blueprint(main_bp)