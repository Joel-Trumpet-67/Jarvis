/**
 * speech.js — STT voice input via Web Speech API.
 *
 * Phase 1: Stub. All functions are no-ops so app.js calls don't crash.
 * Phase 2: Wake word + interim/final transcript state machine replaces this.
 *
 * Exposed as: EigenSpeech
 */

const EigenSpeech = (() => {
  function init()   { /* Phase 2 */ }
  function toggle() {
    EigenTerminal.print('Voice input coming in Phase 2.', 'system');
  }
  function suspend() { /* Phase 2 */ }
  function resume()  { /* Phase 2 */ }

  return { init, toggle, suspend, resume };
})();
