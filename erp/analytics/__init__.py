try:
    from prometheus_client import Gauge  # type: ignore
except Exception:  # pragma: no cover
    class Gauge:  # minimal shim
        def __init__(self, *_a, **_k):
            self.value = 0
        def labels(self, *_a, **_k):  # allow label binding
            return self
        def set(self, v):
            self.value = v
        def inc(self, v=1):
            self.value = getattr(self, "value", 0) + v

MODEL_ACCURACY = Gauge("model_accuracy", "Accuracy of ML model").labels()

def retrain_and_predict(X=None):
    """Very small placeholder used by tests.

    Returns a float-like score and updates a Gauge (or shim).

    """
    # pretend accuracy
    score = 0.93
    try:
        MODEL_ACCURACY.set(score)
    except Exception:
        pass
    return score
