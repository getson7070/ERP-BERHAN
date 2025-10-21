from __future__ import annotations
import hmac, hashlib

def sign_body(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256).hexdigest()
    return f"sha256={mac}"

def verify_signature(headers: dict, body: bytes, secret: str) -> bool:
    sent = headers.get("X-Webhook-Signature") or headers.get("x-webhook-signature") or ""
    expected = sign_body(body, secret)
    # constant-time compare
    return hmac.compare_digest(sent, expected)