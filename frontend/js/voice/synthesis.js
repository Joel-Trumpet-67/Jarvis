/**
 * synthesis.js — TTS output via Web Speech API.
 *
 * Sentence accumulator: buffers streaming tokens and speaks complete
 * sentences as they arrive, so Rocky starts talking before the full
 * response is done streaming.
 *
 * Exposed as: EigenSynthesis
 *   .init()              — call once at boot; selects voice
 *   .beginAccumulating() — called when a streaming response starts
 *   .feedToken(token)    — called for each streamed token
 *   .flush()             — speak any remaining buffer at stream end
 *   .speak(text)         — speak a single string directly
 *   .cancel()            — stop all speech immediately
 */

const EigenSynthesis = (() => {
  const synth = window.speechSynthesis;

  let _voice     = null;   // selected SpeechSynthesisVoice
  let _buffer    = '';     // token accumulator
  let _queue     = [];     // sentence queue (spoken in order)
  let _speaking  = false;  // true while utterance is playing

  // Sentence-ending punctuation that should trigger a speak flush
  const SENTENCE_END = /[.!?]['")\s]|[.!?]$/;

  // ── Voice selection ─────────────────────────────────────────────────

  function init() {
    if (!synth) return;

    // voices may not load synchronously in all browsers
    const _pick = () => {
      const voices = synth.getVoices();
      if (!voices.length) return;

      // Preference order: local male English voices, then any English
      const prefs = [
        v => v.localService && /en[-_]US/i.test(v.lang) && /male|david|mark|guy/i.test(v.name),
        v => v.localService && /en/i.test(v.lang),
        v => /en[-_]US/i.test(v.lang),
        v => /en/i.test(v.lang),
      ];

      for (const test of prefs) {
        const match = voices.find(test);
        if (match) { _voice = match; break; }
      }

      if (!_voice && voices.length) _voice = voices[0];
    };

    _pick();
    if (synth.onvoiceschanged !== undefined) {
      synth.onvoiceschanged = _pick;
    }
  }

  // ── Streaming accumulator ───────────────────────────────────────────

  function beginAccumulating() {
    _buffer = '';
    // Don't clear the queue — let any ongoing speech finish naturally
  }

  function feedToken(token) {
    if (!synth || window.EIGENFORM.isMuted) return;

    _buffer += token;

    // Check if we have a complete sentence to speak
    if (SENTENCE_END.test(_buffer)) {
      // Split at last sentence boundary, keep the rest buffered
      const match = _buffer.match(/^([\s\S]+[.!?]['")\s]?)([\s\S]*)$/);
      if (match) {
        const sentence = match[1].trim();
        _buffer        = match[2];
        if (sentence) _enqueue(sentence);
      }
    }
  }

  function flush() {
    if (!synth || window.EIGENFORM.isMuted) {
      _buffer = '';
      return;
    }
    const remaining = _buffer.trim();
    _buffer = '';
    if (remaining) _enqueue(remaining);
  }

  // ── Direct speak ────────────────────────────────────────────────────

  function speak(text) {
    if (!synth || window.EIGENFORM.isMuted || !text.trim()) return;
    _enqueue(text.trim());
  }

  // ── Cancel ──────────────────────────────────────────────────────────

  function cancel() {
    if (!synth) return;
    _queue   = [];
    _buffer  = '';
    _speaking = false;
    synth.cancel();
    window.EIGENFORM.isSpeaking = false;

    // Resume STT if it was suspended for TTS
    if (typeof EigenSpeech !== 'undefined') EigenSpeech.resume();
  }

  // ── Internal queue ──────────────────────────────────────────────────

  function _enqueue(text) {
    _queue.push(text);
    if (!_speaking) _drainQueue();
  }

  function _drainQueue() {
    if (!_queue.length) {
      _speaking = false;
      window.EIGENFORM.isSpeaking = false;
      // Re-enable mic after TTS finishes
      if (typeof EigenSpeech !== 'undefined') EigenSpeech.resume();
      return;
    }

    _speaking = true;
    window.EIGENFORM.isSpeaking = true;

    // Pause mic while Rocky speaks (prevents feedback loop)
    if (typeof EigenSpeech !== 'undefined') EigenSpeech.suspend();

    const text  = _queue.shift();
    const utt   = new SpeechSynthesisUtterance(text);
    utt.voice   = _voice;
    utt.rate    = 1.0;
    utt.pitch   = 0.9;   // slightly lower — sounds less robotic
    utt.volume  = 1.0;

    utt.onend   = () => _drainQueue();
    utt.onerror = (e) => {
      // 'interrupted' fires when cancel() is called — that's expected
      if (e.error !== 'interrupted') {
        console.warn('[EigenSynthesis] utterance error:', e.error);
      }
      _drainQueue();
    };

    synth.speak(utt);
  }

  return { init, beginAccumulating, feedToken, flush, speak, cancel };
})();
