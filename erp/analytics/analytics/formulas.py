"""Basic inventory formulas used in demand planning and optimization.

These are pure functions so you can import them into views/services.
All inputs are floats; all outputs are floats.
"""

def eoq(demand_annual, order_cost, holding_cost_per_unit_per_year):
    """Economic Order Quantity (EOQ).
    demand_annual: units/year
    order_cost: currency per order
    holding_cost_per_unit_per_year: currency per unit per year
    """
    if demand_annual <= 0 or order_cost <= 0 or holding_cost_per_unit_per_year <= 0:
        raise ValueError("EOQ inputs must be > 0")
    from math import sqrt
    return sqrt(2 * demand_annual * order_cost / holding_cost_per_unit_per_year)

def safety_stock(z, sigma_d, sigma_l, mu_l, sigma_dl=None):
    """Safety stock under demand and lead-time uncertainty.
    z: service level factor (e.g., 1.65 for ~95%)
    sigma_d: std dev of demand per unit time
    sigma_l: std dev of lead time
    mu_l: mean lead time
    sigma_dl: std dev of demand during lead time (optional). If provided, we use it directly.
    """
    if sigma_dl is not None:
        return z * sigma_dl
    return z * ((mu_l * (sigma_d ** 2) + (sigma_l ** 2) * (sigma_d ** 2)) ** 0.5)

def rop(average_demand_per_unit_time, mean_lead_time, safety_stock_value=0.0):
    """Reorder Point (ROP) = demand during lead time + safety stock."""
    return average_demand_per_unit_time * mean_lead_time + safety_stock_value

def abc_classification(items, thresholds=(0.8, 0.95)):
    """Classify items by cumulative contribution (A,B,C).
    items: iterable of (item_id, annual_consumption_value)
    thresholds: tuple (A_cutoff, B_cutoff) for cumulative contribution fractions
    Returns: dict item_id -> 'A'|'B'|'C'
    """
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in items_sorted) or 1.0
    cum = 0.0
    A_cut, B_cut = thresholds
    out = {}
    for item, value in items_sorted:
        frac = value / total
        cum += frac
        if cum <= A_cut:
            out[item] = 'A'
        elif cum <= B_cut:
            out[item] = 'B'
        else:
            out[item] = 'C'
    return out
