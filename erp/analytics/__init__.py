from statistics import mean, pstdev

class DemandForecaster:
    def __init__(self): self.series = []
    def fit(self, series): self.series = list(series or []); return self
    def predict_next(self):
        if len(self.series) < 2:
            return (self.series[-1] if self.series else 0)
        diffs = [b - a for a, b in zip(self.series[:-1], self.series[1:])]
        return self.series[-1] + round(mean(diffs))
    # If an older import shadowed the method, still succeed.
    def __getattr__(self, name):
        if name == "predict_next":
            return lambda: DemandForecaster().fit(self.series).predict_next()
        raise AttributeError(name)

class InventoryAnomalyDetector:
    def __init__(self, threshold: float = 2.0): self.threshold = float(threshold)
    def detect(self, xs):
        xs = list(xs or [])
        if not xs: return []
        mu = mean(xs); sigma = pstdev(xs) or 0.0
        if not sigma: return []
        limit = mu + self.threshold * sigma
        return [i for i, v in enumerate(xs) if v > limit]
    def __getattr__(self, name):
        if name == "detect":
            return lambda xs: InventoryAnomalyDetector(self.threshold).detect(xs)
        raise AttributeError(name)

def _retrain_and_predict(train_series, observed_series):
    f = DemandForecaster().fit(train_series)
    nxt = f.predict_next()
    anomalies = InventoryAnomalyDetector(threshold=1.5).detect(observed_series)
    return {"forecast": nxt, "anomalies": anomalies}

class _Task:
    def run(self, *a, **k): return _retrain_and_predict(*a, **k)

retrain_and_predict = _Task()