# Performance Scoring & Fairness

## Core Principles
1. **Transparency** – every KPI in a scorecard is visible to the subject and tied to a documented metric key.
2. **Consistency** – KPI values come from the unified `AnalyticsFact` table; no duplicate calculations per module.
3. **Directionality** – each KPI declares how it should be scored: `higher_better`, `lower_better`, or `closer_to_target`.
4. **Weighting** – scorecards store weights and targets; totals are weighted averages, capped to avoid runaway scores.

## Bias / Fairness Controls
- KPIs must remain job-relevant (e.g., sales KPIs are not applied to warehouse staff).
- Protected attributes (age, gender, religion, etc.) are excluded from KPIs and ML hints.
- Outliers are capped (ratios max at 2× target) so one KPI cannot dominate the score.
- Missing data impacts only that KPI (scored 0) rather than voiding the evaluation.

## Review Governance
- Evaluations compute automatically but must be reviewed/approved for final decisions.
- 360 feedback is qualitative and cannot reduce a score unless explicitly actioned by HR/admin.

## Auditability
- Each `PerformanceEvaluation` stores `breakdown_json` so totals are reproducible.
- Approval/override actions should be logged through the audit spine for compliance.

## ML Suggestions
- `MLSuggestion` records currently rely on heuristic thresholds; swap in real ML later.
- Always document model inputs/outputs when adding ML to avoid opaque decisions.
