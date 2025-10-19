class DemandForecaster:
    def fit(self, series):
        self.avg = (sum(series) / max(1, len(series))) if series else 0.0
        return self
    def predict(self, n):
        return [self.avg] * int(n)

class InventoryAnomalyDetector:
    def __init__(self, threshold=3.0):
        self.threshold = threshold
    def fit(self, series):
        n = len(series)
        self.mean = (sum(series) / n) if n else 0.0
        self.mad = (sum(abs(x - self.mean) for x in series) / n) if n else 0.0
        return self
    def is_anomalous(self, x):
        return False if self.mad == 0 else abs(x - self.mean) > self.threshold * self.mad


