/**
 * speech.js — Voice input via Web Speech API.
 *
 * Uses continuous mode so it doesn't cut off early.
 * A fresh SpeechRecognition instance is created each session (Chrome
 * silently fails if you call .start() on a reused instance).
 *
 * Silence detection: if no new words arrive for SILENCE_MS, auto-submit.
 *
 * Exposed as: EigenSpeech
 *   .init()    — call once at boot
 *   .toggle()  — start or stop listening
 *   .suspend() — pause (e.g. while Rocky is speaking)
 *   .resume()  — re-enable after suspension
 */

const EigenSpeech = (() => {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  const SILENCE_MS = 1800; // submit after this many ms with no new words

  let _recognition  = null;
  let _listening    = false;
  let _suspended    = false;
  let _supported    = false;
  let _finalText    = '';
  let _silenceTimer = null;

  // ── DOM refs ────────────────────────────────────────────────────────
  let _micBtn    = null;
  let _micStatus = null;
  let _input     = null;

  // ── Init ────────────────────────────────────────────────────────────

  function init() {
    _micBtn    = document.getElementById('micBtn');
    _micStatus = document.getElementById('micStatus');
    _input     = document.getElementById('terminalInput');

    if (!SpeechRecognition) {
      _setStatus('N/A');
      if (_micBtn) {
        _micBtn.disabled = true;
        _micBtn.title    = 'Speech recognition not supported in this browser.';
      }
      return;
    }

    _supported = true;
    _setStatus('IDLE');

    if (_micBtn) _micBtn.addEventListener('click', toggle);
  }

  // ── Controls ────────────────────────────────────────────────────────

  function toggle() {
    if (!_supported) return;
    if (_listening) _stop(true);   // manual stop → submit whatever we have
    else if (!_suspended) _start();
  }

  function suspend() {
    _suspended = true;
    if (_listening) _stop(false);  // stop but don't submit
  }

  function resume() {
    _suspended = false;
  }

  // ── Start — fresh instance every time ───────────────────────────────

  function _start() {
    if (!_supported || _listening) return;

    // Always create a new instance — reusing one after onend breaks in Chrome
    _recognition = new SpeechRecognition();
    _recognition.lang            = 'en-US';
    _recognition.interimResults  = true;
    _recognition.maxAlternatives = 1;
    _recognition.continuous      = true;  // don't cut off on short pauses

    _recognition.onstart = () => {
      _listening = true;
      _finalText = '';
      _setStatus('LISTENING');
      if (_micBtn) _micBtn.classList.add('active');
      if (typeof EigenVisualizer !== 'undefined') EigenVisualizer.start();
    };

    _recognition.onresult = (e) => {
      let interim = '';
      let newFinal = '';

      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) newFinal += t;
        else interim += t;
      }

      if (newFinal) _finalText += newFinal;

      // Show live transcript
      if (_input) _input.value = _finalText + interim;

      // Reset silence timer every time words arrive
      _resetSilenceTimer();
    };

    _recognition.onend = () => {
      // onend fires when the recognizer stops for any reason.
      // If _listening is still true it means it stopped by itself (network
      // hiccup, browser-imposed limit, etc.) — restart it transparently.
      if (_listening && !_suspended) {
        try { _recognition.start(); } catch (_) {}
        return;
      }
      _cleanup();
    };

    _recognition.onerror = (e) => {
      if (e.error === 'not-allowed' || e.error === 'permission-denied') {
        _setStatus('BLOCKED');
        if (typeof EigenTerminal !== 'undefined') {
          EigenTerminal.print(
            'Microphone access denied. Allow it in your browser settings.',
            'error'
          );
        }
        _listening = false;
        _cleanup();
        return;
      }
      // 'no-speech', 'aborted', 'network' etc. — just keep going or clean up
      if (e.error !== 'aborted') {
        console.warn('[EigenSpeech] error:', e.error);
      }
    };

    try {
      _recognition.start();
      _resetSilenceTimer();
    } catch (err) {
      console.warn('[EigenSpeech] start error:', err.message);
    }
  }

  // ── Stop ─────────────────────────────────────────────────────────────

  function _stop(submit) {
    _listening = false;
    _clearSilenceTimer();

    try { _recognition && _recognition.stop(); } catch (_) {}

    if (submit && _finalText.trim()) {
      _submit(_finalText.trim());
    } else {
      _cleanup();
    }
  }

  // ── Silence timer ────────────────────────────────────────────────────

  function _resetSilenceTimer() {
    _clearSilenceTimer();
    _silenceTimer = setTimeout(() => {
      // Silence detected — stop and submit
      _stop(true);
    }, SILENCE_MS);
  }

  function _clearSilenceTimer() {
    if (_silenceTimer) { clearTimeout(_silenceTimer); _silenceTimer = null; }
  }

  // ── Submit + cleanup ─────────────────────────────────────────────────

  function _submit(text) {
    _finalText = '';
    if (_input) _input.value = '';
    _setStatus('PROCESSING');
    _cleanupUI();

    if (typeof EigenApp !== 'undefined') EigenApp.submitMessage(text);
    _setStatus('IDLE');
  }

  function _cleanup() {
    _finalText = '';
    if (_input) _input.value = '';
    _cleanupUI();
    _setStatus('IDLE');
  }

  function _cleanupUI() {
    if (_micBtn) _micBtn.classList.remove('active');
    if (typeof EigenVisualizer !== 'undefined') EigenVisualizer.stop();
  }

  function _setStatus(text) {
    if (_micStatus) _micStatus.textContent = text;
    window.EIGENFORM.micActive = text === 'LISTENING';
  }

  return { init, toggle, suspend, resume };
})();
