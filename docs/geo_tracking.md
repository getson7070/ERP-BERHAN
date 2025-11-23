# Geolocation & Field Tracking

## Capabilities
- Raw ping ingestion with consent enforcement (subject-level opt-in)
- Cached last-known locations for real-time maps
- Task-linked assignments for deliveries and maintenance visits
- ETA and route optimisation with cached fallback when third-party providers are unavailable
- Offline detection that raises audit events when trackers stop reporting

## API Endpoints
- `POST /api/geo/ping` – ingest a ping and refresh cached position
- `GET /api/geo/live` – live last-known positions (filter by task when needed)
- `POST /api/geo/assign` – link a driver/technician to a task with an optional destination
- `GET /api/geo/eta` – ETA from last-known position to a destination or active assignment
- `POST /api/geo/route/optimize` – optimise or cache a route (internal fallback if provider absent)

## Tasks
- `erp.tasks.geo.check_offline_subjects` – raises alerts when an assignment has not pinged recently

## Privacy & Security
- Location usage is blocked when `MarketingConsent.location_opt_in` is false
- Metrics and alerts are logged via `FinanceAuditLog`/`MarketingEvent` without storing sensitive content
- Route and ETA caching is per-tenant via `GeoRouteCache`

## Integration Notes
- If Mapbox is configured (`MAPBOX_TOKEN`), wire the provider inside `optimize_route`.
- Offline alerts can be connected to SMS/Telegram once credentials are provided.
