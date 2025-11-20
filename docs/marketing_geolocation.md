# Marketing & Geolocation

## Entities
- `MarketingCampaign` – campaign header with channel, budget, and A/B flag.
- `MarketingSegment` – JSON-based targeting rules for flexible filtering.
- `MarketingConsent` – opt-in/out for marketing and location data.
- `MarketingEvent` – unified event stream (sent, opened, clicked, converted, geofence_triggered).
- `MarketingGeofence` – radius-based geofences tied to campaigns.
- `MarketingABVariant` – weighted A/B templates.

## Real-time Dashboard
- `GET /api/marketing/campaigns/<id>/stats`
- `GET /api/marketing/campaigns/<id>/stats/stream`
  - SSE feed for live KPI refresh in dashboards.

## Geofencing
- `POST /api/marketing/geofence/campaigns/<campaign_id>`
- `POST /api/marketing/geofence/trigger`
  - Triggered by location pings from apps/bots.
  - Consent enforced: no location use without `location_opt_in=True`.

## A/B Testing
- Variants stored in `MarketingABVariant`.
- `pick_variant()` assigns a variant by weight.
- Variant selection should be stored in `MarketingEvent.metadata_json`.

## Compliance
- Consent table is required for marketing messages and any location-based actions.
- Avoid storing PII in event metadata.
