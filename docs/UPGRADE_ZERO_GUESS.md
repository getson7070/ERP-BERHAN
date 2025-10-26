# ERP-BERHAN Upgrade Pack (Zero-Guess)

This pack was generated **against your uploaded source tree** and paths were verified.

## What this delivers
- Port binding fix: base compose no longer binds host :8000; override publishes **18000:8000**.
- Stable Redis cache service and REDIS_URL wiring for Flask-Limiter.
- Device trust (fingerprint) with endpoints: **/device/trust**, **/device/register**.
- Login UI that hides employee/admin forms unless device is trusted.
- PWA (offline-first) assets: `manifest.webmanifest` + `service-worker.js`.
- Telegram webhook blueprint at **/bot/telegram/webhook** (whitelist via `TELEGRAM_ALLOWED_USER_IDS`).
- One-click reset & seed: `scripts/reset-dev.ps1` (kills port :8000 listeners, builds, seeds).
- Seeded test identities (email / password):  
  - Admin: `admin@local.test` / `Dev!23456`  
  - Employee: `employee@local.test` / `Dev!23456`  
  - Client: `client@local.test` / `Dev!23456`

## Apply
1. **Backup** your repo.
2. Copy the contents of this pack over your repo root, preserving paths.
3. Run:
   ```powershell
   cd <repo-root>
   powershell -ExecutionPolicy Bypass -File scripts\reset-dev.ps1 -HardReset
   ```
4. Open http://localhost:18000/login

## Env
Set as needed:
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USER_IDS=12345678,987654321
```

## Notes
- Fingerprints are hashed via SHA-256 before storage.
- Devices auto-expire after 365 days; revoke by deleting from `trusted_devices`.
- CI can invoke `scripts/reset-dev.ps1` on self-hosted Windows runners or equivalent Bash script for Linux.
