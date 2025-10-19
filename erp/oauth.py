class _OAuth:
    def __init__(self): self._providers = {}
    def register(self, name, **cfg): self._providers[name] = cfg
oauth = _OAuth()


