# Geolocation & Field Tracking

This document describes the current behaviour of the geolocation stack in
ERP-BERHAN: how pings are ingested, how last-known locations are cached,
and how ETAs / routes are calculated.

---

## Capabilities

- Raw ping ingestion with **consent enforcement** (`MarketingConsent`).
- Cached **last-known locations** (`GeoLastLocation`) per subject.
- Task-linked assignments (`GeoAssignment`) for deliveries and maintenance.
- ETA and distance via `eta_seconds` / `haversine_m`.
- Route optimisation via `optimize_route` with cached fallback.
- Audit-trail integration via `AuditLog` on key events.

---

## Data models (high level)

- **GeoPing** – raw ping with `lat`, `lng`, `subject_type`, `subject_id`,
  `source` (app / bot), and timestamp.
- **GeoLastLocation** – denormalised last-known position per subject.
- **GeoAssignment** – links a driver/technician to a task + optional destination.
- **MarketingConsent** – per-user / per-client flag controlling whether marketing /
  tracking pings are allowed.

---

## API Endpoints

All endpoints are exposed via the `geo_api` blueprint:

Base path: **`/api/geo`**

- `POST /api/geo/ping`
  - Ingest a single ping and refresh `GeoLastLocation`.
  - Body:
    - `subject_type`: `"user"` / `"device"` / `"client"` …
    - `subject_id`: integer id.
    - `lat`, `lng`: floats.
    - optional: `label`, `source`.
  - Behaviour:
    - Respects `MarketingConsent` where applicable.
    - Writes an `AuditLog` record for suspicious / blocked pings.

- `GET /api/geo/live`
  - Returns last-known locations from `GeoLastLocation`.
  - Query params (all optional):
    - `subject_type`
    - `subject_id`
  - Use this to build simple “live location” tables or maps.

- `POST /api/geo/assign`
  - Links a subject (driver / technician) to a task or destination.
  - Body:
    - `subject_type`, `subject_id`
    - `entity_type`, `entity_id` (e.g. `"maintenance_ticket"`, `123`)
    - optional `dest_lat`, `dest_lng`.

- `GET /api/geo/eta`
  - Returns ETA / distance between a subject’s last-known location and the
    current assignment / explicit destination.
  - Query params:
    - `subject_type`, `subject_id`
    - optional `dest_lat`, `dest_lng` to override assignment destination.

- `POST /api/geo/route/optimize`
  - Optimises or caches a route and returns ETA/distance details.
  - Body:
    - `origin`: `[lat, lng]`
    - `dest`: `[lat, lng]`
    - optional `waypoints`: list of `[lat, lng]`.

---

## Front-end behaviour

The canonical JS module for app/browser tracking is:

- `static/js/geo-tracking.js` (or equivalent) which:

  1. Uses `navigator.geolocation.getCurrentPosition` with explicit user consent.
  2. Sends `POST /api/geo/ping` with:
     - `subject_type="user"`
     - `subject_id=current_user.id` (injected in the template)
     - `lat`, `lng` from the browser.
  3. Runs on selected pages (marketing & maintenance dashboards), **not globally**.

Example Jinja template snippet:

```html
<script>
  window.ERP_GEO = {
    subjectType: "user",
    subjectId: {{ current_user.id }},
    consent: {{ "true" if current_user.marketing_consent else "false" }},
  };
</script>
<script src="{{ url_for('static', filename='js/geo-tracking.js') }}"></script>
