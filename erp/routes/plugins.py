from flask import Blueprint, render_template
import importlib
import pkgutil
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('plugins', __name__, url_prefix='/plugins')


@bp.route('/')
def index():
    found = []
    try:
        pkg = importlib.import_module('plugins')
        for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + '.'):
            if not ispkg:
                found.append({'name': modname.rsplit('.', 1)[-1], 'module': modname})
    except (ModuleNotFoundError, ImportError) as exc:
        logger.warning("Plugin discovery failed: %s", exc)
    return render_template('plugins/index.html', plugins=found)


@bp.route('/marketplace')
def marketplace():
    try:
        pkg = importlib.import_module('plugins')
        available = [modname for _, modname, _ in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + '.')]
    except (ModuleNotFoundError, ImportError) as exc:
        logger.warning("Marketplace listing failed: %s", exc)
        available = []
    return render_template('plugins/marketplace.html', plugins=available)

