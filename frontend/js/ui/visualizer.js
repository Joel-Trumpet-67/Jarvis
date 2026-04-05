/**
 * visualizer.js — Canvas audio waveform visualizer.
 *
 * Shows animated bars on the #visualizer canvas while the mic is active.
 * Uses Web Audio API (AnalyserNode) for real frequency data.
 * Falls back gracefully if AudioContext is unavailable.
 *
 * Exposed as: EigenVisualizer
 *   .init()   — called at boot; sets up canvas reference
 *   .start()  — begin animation (called when mic starts)
 *   .stop()   — end animation (called when mic stops)
 */

const EigenVisualizer = (() => {
  let _canvas    = null;
  let _ctx       = null;
  let _analyser  = null;
  let _dataArray = null;
  let _animId    = null;
  let _stream    = null;
  let _audioCtx  = null;
  let _running   = false;

  const BAR_COUNT  = 32;
  const BAR_GAP    = 2;

  function init() {
    _canvas = document.getElementById('visualizer');
    if (!_canvas) return;
    _ctx = _canvas.getContext('2d');

    // Keep canvas sharp on HiDPI displays
    const dpr = window.devicePixelRatio || 1;
    _canvas.width  = _canvas.offsetWidth  * dpr;
    _canvas.height = _canvas.offsetHeight * dpr;
    _ctx.scale(dpr, dpr);
  }

  async function start() {
    if (!_canvas || _running) return;
    _running = true;
    _canvas.classList.add('active');

    try {
      _stream   = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const source = _audioCtx.createMediaStreamSource(_stream);
      _analyser = _audioCtx.createAnalyser();
      _analyser.fftSize = 64;
      source.connect(_analyser);
      _dataArray = new Uint8Array(_analyser.frequencyBinCount);
      _draw();
    } catch (_err) {
      // No mic access, or AudioContext unavailable — use fake animation
      _drawFake();
    }
  }

  function stop() {
    _running = false;
    if (_animId) { cancelAnimationFrame(_animId); _animId = null; }
    if (_stream) {
      _stream.getTracks().forEach(t => t.stop());
      _stream = null;
    }
    if (_audioCtx) {
      _audioCtx.close().catch(() => {});
      _audioCtx = null;
    }
    _analyser  = null;
    _dataArray = null;

    if (_canvas) {
      _clear();
      _canvas.classList.remove('active');
    }
  }

  // ── Real frequency data draw ────────────────────────────────────────

  function _draw() {
    if (!_running || !_analyser) return;
    _animId = requestAnimationFrame(_draw);

    _analyser.getByteFrequencyData(_dataArray);
    _render(_dataArray);
  }

  // ── Fake pulsing animation (no AudioContext) ────────────────────────

  let _fakeT = 0;
  function _drawFake() {
    if (!_running) return;
    _animId = requestAnimationFrame(_drawFake);

    _fakeT += 0.08;
    const fake = new Uint8Array(BAR_COUNT);
    for (let i = 0; i < BAR_COUNT; i++) {
      fake[i] = Math.abs(Math.sin(_fakeT + i * 0.4)) * 120 + 30;
    }
    _render(fake);
  }

  // ── Shared render ───────────────────────────────────────────────────

  function _render(data) {
    if (!_ctx || !_canvas) return;
    const W = _canvas.offsetWidth  || _canvas.width;
    const H = _canvas.offsetHeight || _canvas.height;

    _clear();

    const accent = getComputedStyle(document.documentElement)
      .getPropertyValue('--accent').trim() || '#00ffcc';

    const barW = (W - (BAR_COUNT - 1) * BAR_GAP) / BAR_COUNT;
    const step = Math.floor(data.length / BAR_COUNT);

    for (let i = 0; i < BAR_COUNT; i++) {
      const val    = data[i * step] / 255;
      const barH   = Math.max(2, val * H * 0.85);
      const x      = i * (barW + BAR_GAP);
      const y      = (H - barH) / 2;

      _ctx.globalAlpha = 0.5 + val * 0.5;
      _ctx.fillStyle   = accent;
      _ctx.fillRect(x, y, barW, barH);
    }
    _ctx.globalAlpha = 1;
  }

  function _clear() {
    if (_ctx && _canvas) {
      _ctx.clearRect(0, 0, _canvas.offsetWidth, _canvas.offsetHeight);
    }
  }

  return { init, start, stop };
})();
