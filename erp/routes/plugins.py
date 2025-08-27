import importlib
import logging
import pkgutil

from flask import Blueprint, render_template

bp = Blueprint('plugins', __name__, url_prefix='/plugins')


@bp.route('/')
def index():
    found = []
    try:
        pkg = importlib.import_module('plugins')
    except ImportError as exc:
        logging.getLogger(__name__).warning("Plugin import failed: %s", exc)
        return render_template('plugins/index.html', plugins=found)

    for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + '.'):
        if not ispkg:
            found.append({'name': modname.rsplit('.', 1)[-1], 'module': modname})
    return render_template('plugins/index.html', plugins=found)


@bp.route('/marketplace')
def marketplace():
    try:
        pkg = importlib.import_module('plugins')
        available = [modname for _, modname, _ in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + '.')]
    except ImportError as exc:
        logging.getLogger(__name__).warning("Plugin import failed: %s", exc)
        available = []
    return render_template('plugins/marketplace.html', plugins=available)

