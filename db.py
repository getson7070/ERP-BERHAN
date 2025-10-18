import os

def get_dialect(url: str | None = None) -> str:
    url = (url or os.getenv('DATABASE_URL') or 'sqlite:///:memory:')
    scheme = url.split(':', 1)[0]
    if '+' in scheme:
        scheme = scheme.split('+', 1)[0]
    return scheme
