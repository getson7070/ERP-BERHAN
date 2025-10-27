import pkgutil, importlib, inspect
import erp

def test_single_factory_path():
    from erp import create_app
    app = create_app()
    assert app is not None

def test_no_duplicate_factories():
    dup = []
    for _, name, _ in pkgutil.walk_packages(erp.__path__, erp.__name__ + '.'):
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        for _, obj in inspect.getmembers(mod, inspect.isfunction):
            if obj.__name__ == 'create_app':
                dup.append(f'{obj.__module__}.create_app')
    assert dup == ['erp.app.create_app'], f'Duplicate factories: {dup}'
