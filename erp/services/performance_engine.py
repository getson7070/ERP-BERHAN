"""Scorecard computation using analytics facts."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Tuple

from erp.models import AnalyticsFact, KPIRegistry, ScorecardTemplate


def _score_value(
    value: Decimal,
    target: Decimal | None,
    direction: str,
    min_score: Decimal,
    max_score: Decimal,
) -> Decimal:
    """Map a raw KPI value to a bounded score respecting directionality."""

    if value is None:
        return Decimal("0")

    if direction == "higher_better":
        if target and target > 0:
            ratio = min(Decimal("2.0"), value / target)
            return min_score + (max_score - min_score) * ratio / Decimal("2.0")
        return min(max_score, max(min_score, value))

    if direction == "lower_better":
        if target and target > 0:
            ratio = min(Decimal("2.0"), target / max(value, Decimal("0.0001")))
            return min_score + (max_score - min_score) * ratio / Decimal("2.0")
        return max(min_score, max_score - value)

    if direction == "closer_to_target" and target is not None:
        diff = abs(value - target)
        score = max_score - diff
        return max(min_score, min(max_score, score))

    return Decimal("0")


def compute_scorecard(
    org_id: int,
    template: ScorecardTemplate,
    subject_type: str,
    subject_id: int,
    start_date: date,
    end_date: date,
) -> Tuple[Decimal, dict]:
    """Aggregate KPIs from facts, score them, and return total + breakdown."""

    total_weight = Decimal("0")
    weighted_sum = Decimal("0")
    breakdown: dict[str, dict] = {}

    for item in template.items:
        kpi = KPIRegistry.query.filter_by(org_id=org_id, kpi_key=item.kpi_key, is_active=True).first()
        if not kpi:
            continue

        weight = Decimal(str(item.weight_override or kpi.weight or 1))
        target = item.target_override or kpi.target_value

        q = AnalyticsFact.query.filter(
            AnalyticsFact.org_id == org_id,
            AnalyticsFact.metric_key == item.kpi_key,
            AnalyticsFact.ts_date >= start_date,
            AnalyticsFact.ts_date <= end_date,
        )

        if subject_type == "employee":
            q = q.filter(AnalyticsFact.user_id == subject_id)
        elif subject_type == "client":
            q = q.filter(AnalyticsFact.client_id == subject_id)
        elif subject_type in {"inventory", "item"}:
            q = q.filter(AnalyticsFact.item_id == subject_id)
        elif subject_type == "warehouse":
            q = q.filter(AnalyticsFact.warehouse_id == subject_id)

        values = [Decimal(str(x.value)) for x in q.all()]
        raw = sum(values) / Decimal(len(values)) if values else Decimal("0")

        score = _score_value(raw, target, kpi.direction, kpi.min_score, kpi.max_score)

        breakdown[item.kpi_key] = {
            "raw": float(raw),
            "target": float(target) if target is not None else None,
            "score": float(score),
            "weight": float(weight),
            "direction": kpi.direction,
        }

        total_weight += weight
        weighted_sum += score * weight

    total_score = (weighted_sum / total_weight) if total_weight > 0 else Decimal("0")
    return total_score, breakdown
