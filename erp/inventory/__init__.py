from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class Lot:
    sku: str
    lot: str
    expiry: date

def assign_lot(sku: str, lot: str, days_valid: int = 30) -> Lot:
    return Lot(sku=sku, lot=lot, expiry=date.today() + timedelta(days=days_valid))

def check_expiry(lot: Lot) -> bool:
    return lot.expiry < date.today()


