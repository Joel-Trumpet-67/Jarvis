/**
 * hud.js — HUD live clock and connection status indicator.
 *
 * Phase 1: Clock + status polling (fully working).
 * Phase 6: Additional HUD panels, mode indicators added.
 *
 * Exposed as: EigenHUD
 */

const EigenHUD = (() => {
  const STATUS_POLL_INTERVAL_MS = 30_000; // 30 seconds

  let _clockInterval  = null;
  let _statusInterval = null;

  // ── Clock ─────────────────────────────────────────────────────

  function _updateClock() {
    const el = document.getElementById('hudClock');
    if (!el) return;
    const now = new Date();
    const hh  = String(now.getHours()).padStart(2, '0');
    const mm  = String(now.getMinutes()).padStart(2, '0');
    const ss  = String(now.getSeconds()).padStart(2, '0');
    el.textContent = `${hh}:${mm}:${ss}`;
  }

  // ── Status ring ───────────────────────────────────────────────

  function setStatus(state) {
    // state: 'online' | 'offline' | 'connecting'
    const ring = document.getElementById('statusRing');
    const text = document.getElementById('statusText');
    if (!ring || !text) return;

    ring.className = `status-ring ${state}`;

    const labels = {
      online:     'ONLINE',
      offline:    'OFFLINE',
      connecting: 'CONNECTING',
    };
    text.textContent = labels[state] || state.toUpperCase();
    window.EIGENFORM.modelOnline = state === 'online';
  }

  async function _pollStatus() {
    try {
      const data = await EigenClient.getStatus();
      setStatus(data.model_reachable ? 'online' : 'offline');
    } catch (_) {
      setStatus('offline');
    }
  }

  // ── Public API ────────────────────────────────────────────────

  function start() {
    // Start clock — updates every second
    _updateClock();
    _clockInterval = setInterval(_updateClock, 1000);

    // Poll backend status immediately, then every 30s
    _pollStatus();
    _statusInterval = setInterval(_pollStatus, STATUS_POLL_INTERVAL_MS);
  }

  function stop() {
    clearInterval(_clockInterval);
    clearInterval(_statusInterval);
  }

  return { start, stop, setStatus };
})();
