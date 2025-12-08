# Layer 8 Audit – Geo Engine & Tracking (Beyond Maintenance)

## Scope
Assess live geolocation ingestion, route optimization, consent, and assignment capabilities beyond maintenance, including sales visits and task tracking.

## Current Capabilities
- **Geo ping ingestion with consent checks**: `/api/geo/ping` stores immutable pings, updates last-known locations, and enforces consent for non-field users while allowing privileged roles to submit on behalf of others.【F:erp/routes/geo_api.py†L1-L123】
- **Last-location and assignment serializers**: Geo API provides structured responses for last-known locations and assignments with ETA utilities, enabling downstream routing/dispatch features.【F:erp/routes/geo_api.py†L1-L74】
- **Marketing consent integration**: Geo consent is verified via `MarketingConsent.location_opt_in`, distinguishing operational tracking for sales/marketing staff from marketing opt-in requirements.【F:erp/routes/geo_api.py†L34-L123】

## Gaps & Risks vs. Requirements
- **Sales/maintenance visit capture**: No explicit endpoints for logging institutional visits with geo stamps tied to orders or maintenance tickets; requirement expects visit capture with location.
- **Supervisor/admin visibility**: Dashboards for supervisors/admins to view live maps, breach alerts, and path histories are absent; no MFA gating for high-privilege geo views.
- **Geo-linked approvals**: Approvals (orders/maintenance/procurement) do not enforce geo metadata; geo engine is not wired into workflow audit trails.
- **Data retention & privacy**: Retention limits, privacy controls, and aggregation for location data are unspecified, posing compliance risk.
- **UI/UX**: Lacks modern map UX with clustering, mobile-ready controls, offline caching, and accessibility features.

## Recommendations
1. **Visit logging APIs** for sales/maintenance with org-scoped order/ticket linkage, mandatory geo stamp, and audit logging; expose supervisor review views.
2. **Geo overlays in workflows**: Require geo metadata on approvals/hand-offs; show live location and ETA on order/maintenance/procurement dashboards.
3. **Access controls + MFA**: Protect geo dashboards and location history with supervisor/admin roles plus MFA and consent auditing.
4. **Retention and privacy policies**: Define TTLs, aggregation, and subject export/deletion flows to comply with data minimization.
5. **Modern geo UX**: Map-based dashboards with clustering, filters, mobile optimization, and offline-friendly background pings; align styling with current UI standards.
