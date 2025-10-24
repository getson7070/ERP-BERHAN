# Basic contracts (app factory + health endpoints)
import importlib, sys
def fail(msg, e=None):
    print('[contract] FAIL:', msg, e or '')
    sys.exit(1)
try:
    erp = importlib.import_module('erp')
    create_app = getattr(erp, 'create_app')
    app = create_app(testing=True) if 'testing' in create_app.__code__.co_varnames else create_app()
    print('[contract] app factory OK')
except Exception as e:
    fail('app factory', e)
client = app.test_client()
oks = 0
for path in ('/status','/health','/ops/doctor'):
    try:
        r = client.get(path)
        if r.status_code < 500:
            oks += 1
    except Exception as e:
        pass
print('[contract] reachable health-like endpoints:', oks)
if oks < 1: fail('no health-like endpoint responded OK')
print('[contract] PASS')
