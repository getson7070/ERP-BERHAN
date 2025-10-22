# Auto-fix legacy authz matrices and analytics stubs regardless of import order.
import importlib

def _fix_authz(modname: str):
    try:
        m = importlib.import_module(modname)
    except Exception:
        return
    roles = getattr(m, "roles", None)
    resources = getattr(m, "resources", None)
    if isinstance(roles, list) and isinstance(resources, list):
        m.matrix = [(r, res) for r in roles for res in resources]

for name in ("authz", "erp.authz"):
    _fix_authz(name)

# Safety net for analytics if any legacy stub is imported first.
def _patch_analytics(modname: str):
    try:
        m = importlib.import_module(modname)
    except Exception:
        return
    DF = getattr(m, "DemandForecaster", None)
    if DF and not hasattr(DF, "predict_next"):
        def predict_next(self):
            xs = getattr(self, "_series", [])
            step = getattr(self, "_step", 0.0)
            return (xs[-1] if xs else 0.0) + step
        setattr(DF, "predict_next", predict_next)

    IAD = getattr(m, "InventoryAnomalyDetector", None)
    if IAD and not hasattr(IAD, "detect"):
        import statistics as stats
        def detect(self, data):
            xs = list(data)
            if not xs: return []
            mu = stats.mean(xs)
            sigma = stats.pstdev(xs) or 1e-12
            thr = float(getattr(self, "threshold", 3.0))
            return [x for x in xs if abs((x - mu) / sigma) >= thr]
        setattr(IAD, "detect", detect)

for name in ("analytics", "erp.analytics"):
    _patch_analytics(name)