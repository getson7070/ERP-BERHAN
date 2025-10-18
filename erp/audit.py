import hashlib, hmac

def log_audit(entries: list[dict], record: dict, secret: str = 'k') -> list[dict]:
    prev = entries[-1]['h'] if entries else ''
    payload = (prev + repr(sorted(record.items()))).encode('utf-8')
    h = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    out = {**record, 'h': h}
    entries.append(out)
    return entries

def check_audit_chain(entries: list[dict], secret: str = 'k') -> bool:
    test: list[dict] = []
    for e in entries:
        rec = {k: v for k, v in e.items() if k != 'h'}
        test = log_audit(test, rec, secret)
        if test[-1]['h'] != e['h']:
            return False
    return True
