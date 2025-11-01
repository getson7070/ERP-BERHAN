"""
inventory package facade:
Ensures `from erp.inventory import Lot, Serial` never raises ImportError.
If real models are present (in common locations), they are re-exported;
otherwise placeholders are provided so imports still work.
"""
from importlib import import_module

Lot = None
Serial = None

_candidates = [
    (".models", "Lot"),
    (".models", "Serial"),
    (".lot", "Lot"),
    (".serial", "Serial"),
]

for mod, attr in _candidates:
    try:
        m = import_module(mod, __name__)
        val = getattr(m, attr, None)
        if attr == "Lot" and val is not None:
            Lot = val
        if attr == "Serial" and val is not None:
            Serial = val
    except Exception:
        pass

if Lot is None:
    class Lot:  # placeholder
        __doc__ = "Placeholder for erp.inventory.Lot; real model not available."

if Serial is None:
    class Serial:  # placeholder
        __doc__ = "Placeholder for erp.inventory.Serial; real model not available."

__all__ = ["Lot", "Serial"]
