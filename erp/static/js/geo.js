// Lightweight browser-side geolocation helper for ERP-BERHAN.
//
// Behaviour:
// - Runs on every page (via base.html include), but safely no-ops when:
//   * User is not authenticated, or
//   * Browser does not support navigator.geolocation, or
//   * Current user id cannot be resolved.
// - Sends pings to /api/geo/ping with subject_type="user" and subject_id=current_user.id
//   by default, unless overridden via window.ERP_GEO.
// - Respects backend consent and RBAC. If the backend responds with 204/no_location_consent
//   or 403, the helper quietly stops without breaking the UI.
//
// Configuration via window.ERP_GEO (optional):
//   window.ERP_GEO = {
//     subjectType: "user",         // default
//     subjectId: 123,              // default: current_user.id from body[data-current-user-id]
//     autoStart: true,             // default true; set to false to fully opt-out for this page
//     intervalMs: 300000,          // default 5 minutes between pings
//     debug: false                 // when true, logs extra info to console
//   };
//
// IMPORTANT:
// - Geolocation is operationally mandatory for sales & marketing. That enforcement happens on
//   the backend (geo_api.ping) based on the user's roles.
// - This helper simply sends pings; the server decides which ones to honour.

(function () {
  const body = document.body;
  if (!body) return;

  const isAuthenticated = body.dataset.isAuthenticated === '1';
  if (!isAuthenticated) {
    return;
  }

  if (!('geolocation' in navigator)) {
    return;
  }

  const cfg = window.ERP_GEO || {};
  const userIdRaw = cfg.subjectId != null ? cfg.subjectId : body.dataset.currentUserId;
  const subjectId = Number(userIdRaw || 0);
  const subjectType = cfg.subjectType || 'user';
  const autoStart = cfg.autoStart !== false;  // default true
  const intervalMs = Number(cfg.intervalMs || 300000); // 5 minutes
  const debug = !!cfg.debug;

  if (!subjectId || !autoStart) {
    if (debug) {
      console.info('[geo] Skipping auto-start: subjectId or autoStart not set', {
        subjectId,
        autoStart
      });
    }
    return;
  }

  function logDebug(message, extra) {
    if (!debug) return;
    if (extra) {
      console.debug('[geo]', message, extra);
    } else {
      console.debug('[geo]', message);
    }
  }

  async function sendPing(position) {
    try {
      const coords = position.coords || {};
      const payload = {
        subject_type: subjectType,
        subject_id: subjectId,
        lat: coords.latitude,
        lng: coords.longitude,
        accuracy_m: coords.accuracy,
        speed_mps: coords.speed,
        heading_deg: coords.heading,
        source: 'browser'
      };
      logDebug('Sending ping', payload);
      const resp = await fetch('/api/geo/ping', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(payload)
      });
      if (resp.status === 204) {
        // No consent / ignored. Quietly stop.
        logDebug('Ping ignored by backend (no_location_consent/204). Stopping.');
        return false;
      }
      if (resp.status === 403) {
        // Forbidden by RBAC. Stop trying.
        logDebug('Ping forbidden by backend (403). Stopping.');
        return false;
      }
      // Any 2xx other than 204 is OK; we keep going.
      return true;
    } catch (err) {
      logDebug('Error while sending ping', err);
      return false;
    }
  }

  function requestAndSendPing() {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        sendPing(position);
      },
      (error) => {
        // User can deny, timeout, etc. We intentionally do not spam alerts.
        logDebug('Geolocation error', error);
      },
      {
        enableHighAccuracy: true,
        maximumAge: 60000,
        timeout: 10000
      }
    );
  }

  // Initial ping + interval-based refresh.
  requestAndSendPing();
  if (intervalMs > 0) {
    setInterval(requestAndSendPing, intervalMs);
  }
})();
