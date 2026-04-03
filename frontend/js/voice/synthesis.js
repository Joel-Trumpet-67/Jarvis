/**
 * synthesis.js — TTS output via Web Speech API.
 *
 * Phase 1: Stub. All functions are no-ops so app.js calls don't crash.
 * Phase 2: Full sentence-accumulator implementation replaces this.
 *
 * Exposed as: EigenSynthesis
 */

const EigenSynthesis = (() => {
  function init()              { /* Phase 2 */ }
  function beginAccumulating() { /* Phase 2 */ }
  function feedToken(token)    { /* Phase 2 */ }
  function flush()             { /* Phase 2 */ }
  function speak(text)         { /* Phase 2 */ }
  function cancel()            {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  }

  return { init, beginAccumulating, feedToken, flush, speak, cancel };
})();
