from functools import wraps
from flask import session, redirect, url_for
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import bcrypt

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


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('auth.choose_login'))
        return f(*args, **kwargs)
    return wrap
