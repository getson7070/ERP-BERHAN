"""Lightweight NLP intent parsing for bot commands."""
from __future__ import annotations

import re
from typing import Optional

INTENT_RULES = [
    (r"\bapprove\b|\bconfirm\b", "approve_action"),
    (r"\breject\b|\bdecline\b", "reject_action"),
    (r"\binventory\b|\bstock\b", "inventory_query"),
    (r"\breorder\b|\bstock\s*alert\b", "inventory_reorder"),
    (r"\bcash\b|\bbalance\b", "finance_cash_query"),
    (r"\bstatement\b", "bank_statement"),
    (r"\breport\b|\bend of day\b|\bdaily plan\b", "report_submit"),
    (r"\banalytics\b|\bperformance\b|\bscore\b", "analytics_query"),
]


def parse_intent(text: str) -> Optional[str]:
    """Return the first matching intent for *text*, or ``None`` if unknown."""

    cleaned = (text or "").lower().strip()
    for pattern, intent in INTENT_RULES:
        if re.search(pattern, cleaned):
            return intent
    return None
