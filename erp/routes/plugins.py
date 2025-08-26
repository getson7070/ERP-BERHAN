from flask import Blueprint, render_template
import importlib
import pkgutil

bp = Blueprint('plugins', __name__, url_prefix='/plugins')


@bp.route('/')
def index():
    found = []
    try:
        pkg = importlib.import_module('plugins')
        for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + '.'):
            if not ispkg:
                found.append({'name': modname.rsplit('.', 1)[-1], 'module': modname})
    except Exception:
        pass
    return render_template('plugins/index.html', plugins=found)


@bp.route('/marketplace')
def marketplace():
    try:
        pkg = importlib.import_module('plugins')
        available = [modname for _, modname, _ in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + '.')]
    except Exception:
        available = []
    return render_template('plugins/marketplace.html', plugins=available)

