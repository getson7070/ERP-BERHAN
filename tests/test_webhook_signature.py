import os, hmac, hashlib, pathlib, sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from erp import create_app

def test_webhook_hmac(monkeypatch):
    monkeypatch.setenv('API_TOKEN','tok')
    app = create_app(); app.config['TESTING']=True
    app.config['WEBHOOK_SECRET']='secret'
    client = app.test_client()
    payload = b'{"a":1}'
    sig = hmac.new(b'secret', payload, hashlib.sha256).hexdigest()
    resp = client.post('/api/webhook/test', data=payload, headers={'Authorization':'Bearer tok','X-Signature':sig,'Content-Type':'application/json'})
    assert resp.status_code==200
    bad = client.post('/api/webhook/test', data=payload, headers={'Authorization':'Bearer tok','X-Signature':'bad','Content-Type':'application/json'})
    assert bad.status_code==401
