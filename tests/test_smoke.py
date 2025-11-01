import re, pathlib
from erp import create_app

def test_health_ok():
    c = create_app().test_client()
    assert c.get('/health').status_code == 200
    assert c.get('/health/ready').status_code == 200

def test_no_obvious_stubs():
    root = pathlib.Path('erp')
    bad = []
    for p in root.rglob('*.py'):
        t = p.read_text(encoding='utf-8', errors='ignore')
        if re.search(r'raise\s+NotImplementedError|pass\s+#\s*TODO', t):
            bad.append(str(p))
    assert not bad, f'Stubs found: {bad}'
