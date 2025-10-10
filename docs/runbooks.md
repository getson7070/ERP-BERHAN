# Runbooks

## Login failures spike
- Check CI deploy recency
- Sentry: filter `auth_mfa_fail` and `auth_failure` rates
- Confirm rate-limit not throttling legit IP ranges
- Validate clock skew on servers (NTP)

## Telegram alerts stopped
- Check metrics `telegram_send_fail`
- Verify outbound egress + Telegram API availability
- Rotate token only if suspected compromise (follow secrets SOP)

## DB saturation
- Inspect slow queries; ensure indexes
- Scale DB instance or add read replica (cloud managed)
