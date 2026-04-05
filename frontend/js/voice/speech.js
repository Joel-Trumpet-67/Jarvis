/**
 * speech.js — Voice input via Web Speech API.
 *
 * One-shot mode: click → listen → silence detected → auto-submit.
 * Interim transcripts show in the input field while speaking.
 * Clicking the mic button while listening cancels the session.
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

  let _recognition  = null;
  let _listening    = false;   // currently running a recognition session
  let _suspended    = false;   // suppressed while TTS is playing
  let _supported    = false;
  let _finalText    = '';      // accumulates confirmed words

  // ── DOM refs (set in init) ──────────────────────────────────────────
  let _micBtn    = null;
  let _micStatus = null;
  let _input     = null;

  // ── Setup ───────────────────────────────────────────────────────────

  function init() {
    _micBtn    = document.getElementById('micBtn');
    _micStatus = document.getElementById('micStatus');
    _input     = document.getElementById('terminalInput');

    if (!SpeechRecognition) {
      _setStatus('MIC: N/A');
      if (_micBtn) {
        _micBtn.disabled = true;
        _micBtn.title    = 'Speech recognition not supported in this browser.';
      }
      return;
    }

    _supported = true;
    _setStatus('MIC: IDLE');

    _recognition = new SpeechRecognition();
    _recognition.lang           = 'en-US';
    _recognition.interimResults = true;
    _recognition.maxAlternatives = 1;
    _recognition.continuous     = false; // auto-stop on silence

    _recognition.onstart = () => {
      _listening = true;
      _finalText = '';
      _setStatus('MIC: LISTENING');
      if (_micBtn) _micBtn.classList.add('active');
      if (typeof EigenVisualizer !== 'undefined') EigenVisualizer.start();
    };

    _recognition.onresult = (e) => {
      let interim = '';
      _finalText  = '';

      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) {
          _finalText += t;
        } else {
          interim += t;
        }
      }

      // Show live transcript in the input field
      if (_input) _input.value = _finalText || interim;
    };

    _recognition.onend = () => {
      _listening = false;
      if (_micBtn) _micBtn.classList.remove('active');
      if (typeof EigenVisualizer !== 'undefined') EigenVisualizer.stop();

      if (_finalText.trim()) {
        _setStatus('MIC: PROCESSING');
        const text  = _finalText.trim();
        _finalText  = '';
        if (_input)  _input.value = '';

        // Submit through the same pipeline as typed input
        if (typeof EigenApp !== 'undefined') {
          EigenApp.submitMessage(text);
        }
        _setStatus('MIC: IDLE');
      } else {
        _setStatus('MIC: IDLE');
        if (_input) _input.value = '';
      }
    };

    _recognition.onerror = (e) => {
      _listening = false;
      if (_micBtn) _micBtn.classList.remove('active');
      if (typeof EigenVisualizer !== 'undefined') EigenVisualizer.stop();

      switch (e.error) {
        case 'not-allowed':
        case 'permission-denied':
          _setStatus('MIC: BLOCKED');
          if (typeof EigenTerminal !== 'undefined') {
            EigenTerminal.print(
              'Microphone access denied. Allow it in your browser settings.',
              'error'
            );
          }
          break;
        case 'no-speech':
          _setStatus('MIC: IDLE');
          break;
        case 'aborted':
          _setStatus('MIC: IDLE');
          break;
        default:
          _setStatus('MIC: ERR');
          console.warn('[EigenSpeech] error:', e.error);
      }
    };

    // Wire mic button
    if (_micBtn) {
      _micBtn.addEventListener('click', toggle);
    }
  }

  // ── Controls ────────────────────────────────────────────────────────

  function toggle() {
    if (!_supported) return;
    if (_listening) {
      _stop();
    } else if (!_suspended) {
      _start();
    }
  }

  function suspend() {
    _suspended = true;
    if (_listening) _stop();
  }

  function resume() {
    _suspended = false;
  }

  // ── Internals ───────────────────────────────────────────────────────

  function _start() {
    if (!_supported || _listening) return;
    try {
      _recognition.start();
    } catch (err) {
      // Can happen if recognition is mid-abort — ignore
      console.warn('[EigenSpeech] start error:', err.message);
    }
  }

  function _stop() {
    if (!_supported || !_listening) return;
    try {
      _recognition.stop(); // triggers onend
    } catch (_) { /* ignore */ }
  }

  function _setStatus(text) {
    if (_micStatus) _micStatus.textContent = text;
    window.EIGENFORM.micActive = text === 'MIC: LISTENING';
  }

  return { init, toggle, suspend, resume };
})();
