# Integration API

The integration API exposes REST and GraphQL endpoints for connecting
third‑party services. Access requires the global API token and an **Admin**
role.

## REST events

`POST /api/integrations/events`

Send webhook‑style events. The payload must include an `event` string and a
`payload` object.

## GraphQL

`POST /api/integrations/graphql`

Supports a minimal schema for querying supported events. Depth and complexity
limits from the core API apply to guard against abuse.
