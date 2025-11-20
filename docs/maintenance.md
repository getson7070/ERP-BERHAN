# Maintenance & Asset Management

## 1. Assets

- Entity: `MaintenanceAsset`
- Key fields: code, name, category, location, purchase cost, salvage value, useful life, depreciation_method, is_critical
- Endpoints: `GET /api/maintenance/assets`, `POST /api/maintenance/assets`

## 2. Preventive Schedules

- Entity: `MaintenanceSchedule`
- Types: time-based today; usage hooks are present for future expansion
- Daily task `generate_scheduled_work_orders` auto-creates preventive WOs on `next_due_date`
- Endpoint: `POST /api/maintenance/assets/<asset_id>/schedules`

## 3. Work Orders

- Entity: `MaintenanceWorkOrder`
- Flow: `open` → `in_progress` → `completed` (or `cancelled`)
- Tracks downtime (`downtime_start` → `downtime_end` → `downtime_minutes`) and costs (labor/material/other/total)
- Timeline events: `MaintenanceEvent` records status changes and escalations
- Endpoints: `POST /api/maintenance/work-orders`, `/api/maintenance/work-orders/<id>/start`, `/api/maintenance/work-orders/<id>/complete`

## 4. Escalation

- Rules: `MaintenanceEscalationRule` filter by asset or category with downtime thresholds
- Events: `MaintenanceEscalationEvent` records triggered rules; `check_escalations` Celery task evaluates every cycle
- Notification channel placeholder: `notify_channel` (telegram/email/SMS/dashboard)

## 5. KPIs & Analytics

- Endpoint: `GET /api/maintenance/kpi/summary?from=YYYY-MM-DD&to=YYYY-MM-DD`
- Returns: total_downtime_minutes, mttr_minutes, avg_response_minutes, total_cost

## 6. Sensor Data

- Entity: `MaintenanceSensorReading`
- Purpose: store optional IoT telemetry (temperature, vibration, error codes) for future predictive maintenance models.
