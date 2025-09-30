from functools import wraps
from typing import Callable, Iterable, Optional
from flask import session, redirect, url_for, flash
from argon2 import PasswordHasher

_hasher = PasswordHasher()  # strong defaults

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except Exception:
        return False

def login_required(view: Callable):
    @wraps(view)
    def wrapper(*a, **k):
        if not session.get("logged_in"):
            flash("Please log in.")
            return redirect(url_for("auth.choose_login"))
        return view(*a, **k)
    return wrapper

def roles_required(*roles: Iterable[str]):
    roles = set(roles)
    def deco(view: Callable):
        @wraps(view)
        def wrapper(*a, **k):
            role = session.get("role")
            if role not in roles:
                flash("Not authorized.")
                return redirect(url_for("main.dashboard"))
            return view(*a, **k)
        return wrapper
    return deco

def has_permission(name: str) -> bool:
    perms = session.get("permissions") or []
    return name in perms
