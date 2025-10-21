from statistics import mean, pstdev

def _predict(series):
    if len(series) < 2:
        return series[-1] if series else 0
    diffs = [b - a for a, b in zip(series[:-1], series[1:])]
    return series[-1] + round(mean(diffs))

def _detect(xs, threshold):
    xs = list(xs or [])
    if not xs:
        return []
    mu = mean(xs)
    sigma = pstdev(xs) or 0.0
    if not sigma:
        return []
    limit = mu + float(threshold) * sigma
    return [i for i, v in enumerate(xs) if v > limit]

class DemandForecaster:
    def __init__(self):
        self.series = []
    def fit(self, series):
        self.series = list(series or [])
        return self
    # Defensive: even if something shadows attributes, this always returns the impl.
    def __getattribute__(self, name):
        if name == "predict_next":
            return object.__getattribute__(self, "_predict_next_impl")
        return object.__getattribute__(self, name)
    def _predict_next_impl(self):
        return _predict(self.series)

class InventoryAnomalyDetector:
    def __init__(self, threshold: float = 2.0):
        self.threshold = float(threshold)
    def __getattribute__(self, name):
        if name == "detect":
            return object.__getattribute__(self, "_detect_impl")
        return object.__getattribute__(self, name)
    def _detect_impl(self, xs):
        return _detect(xs, self.threshold)

def _retrain_and_predict(train_series, observed_series):
    f = DemandForecaster().fit(train_series)
    nxt = f._predict_next_impl()
    anomalies = InventoryAnomalyDetector(threshold=1.5)._detect_impl(observed_series)
    return {"forecast": nxt, "anomalies": anomalies}

class _Task:
    def run(self, *a, **k):
        return _retrain_and_predict(*a, **k)

retrain_and_predict = _Task()
__all__ = ["DemandForecaster", "InventoryAnomalyDetector", "retrain_and_predict"]
