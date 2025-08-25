from flask import Blueprint, request, redirect, url_for, flash
import secrets
from datetime import datetime, timedelta
from db import get_db

auth_bp = Blueprint('auth', __name__)



@auth_bp.route('/password_reset', methods=['POST'])
def password_reset():
    email = request.form.get('email')
    token = secrets.token_urlsafe(16)
    expires = datetime.now() + timedelta(hours=1)
    conn = get_db()
    user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if user:
        conn.execute('INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)',
                     (user['id'], token, expires))
        conn.commit()
        print(f"Password reset token for {email}: {token}")
        flash('Password reset link has been sent to your email.')
    else:
        flash('Email not found.')
    conn.close()
    return redirect(request.referrer or url_for('choose_login'))
