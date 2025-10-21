from ..celery_app import celery
import statistics as stats

class DemandForecaster:
    def __init__(self): self.s=[]
    def fit(self, series): self.s=list(series); return self
    def predict_next(self):
        if not self.s: return 0
        if len(self.s)==1: return self.s[0]
        return self.s[-1] + (self.s[-1]-self.s[0])/(len(self.s)-1)

class InventoryAnomalyDetector:
    def __init__(self, threshold=1.0): self.t=threshold
    def detect(self, data):
        if not data: return []
        mu=stats.mean(data); sd=stats.pstdev(data) or 1.0
        return [i for i,x in enumerate(data) if abs(x-mu)/sd > self.t]

@celery.task
def retrain_and_predict(history, observed):
    f=DemandForecaster().fit(history)
    return {"next": f.predict_next(), "anomalies": InventoryAnomalyDetector(1.5).detect(observed)}

def kpi_staleness_seconds():  # used by /metrics
    return 0.0
