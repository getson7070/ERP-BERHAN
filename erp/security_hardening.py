# generated 20251027_105458
import os, shlex, subprocess as _sp
from markupsafe import escape
from flask import render_template_string as _rts

def safe_run(args, **kwargs):
    if isinstance(args, str):
        # block shell-string usage
        raise ValueError("Pass a list of args; shell strings are not allowed")
    kwargs.setdefault("shell", False)
    kwargs.setdefault("check", True)
    return _sp.run(args, **kwargs)

def safe_call(args, **kwargs):
    if isinstance(args, str):
        raise ValueError("Pass a list of args; shell strings are not allowed")
    kwargs.setdefault("shell", False)
    return _sp.call(args, **kwargs)

def safe_popen(args, **kwargs):
    if isinstance(args, str):
        raise ValueError("Pass a list of args; shell strings are not allowed")
    kwargs.setdefault("shell", False)
    return _sp.Popen(args, **kwargs)

def safe_render_template_string(template_src: str, **context):
    # Escape all values passed from python to reduce injection surface.
    safe_ctx = {k: (escape(v) if not hasattr(v, "__html__") else v) for k, v in context.items()}
    return _rts(template_src, **safe_ctx)

def env_database_url(default=None):
    v = os.environ.get("DATABASE_URL", default)
    if not v:
        raise RuntimeError("DATABASE_URL is not set")
    return v

def env_secret_key(default=None):
    v = os.environ.get("SECRET_KEY", default)
    if not v:
        raise RuntimeError("SECRET_KEY is not set")
    return v

