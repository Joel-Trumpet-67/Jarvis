/**
 * app.js — Application startup logic.
 *
 * Called by main.js after DOMContentLoaded.
 * Responsible for:
 *   1. Generating or restoring the session ID
 *   2. Fetching session history from backend (backend = source of truth)
 *   3. Playing boot sequence if no history exists
 *   4. Wiring all UI event listeners
 *   5. Starting HUD updates
 */

const EigenApp = (() => {

  /** Generate a simple unique session ID. */
  function _generateSessionId() {
    return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7);
  }

  /** Get or create session ID from sessionStorage. */
  function _initSessionId() {
    let id = sessionStorage.getItem('eigenform_session_id');
    if (!id) {
      id = _generateSessionId();
      sessionStorage.setItem('eigenform_session_id', id);
    }
    window.EIGENFORM.sessionId = id;
  }

  /** Fetch session history and render it, or play boot sequence. */
  async function _restoreOrBoot() {
    const data = await EigenClient.getSession();

    if (data.messages && data.messages.length > 0) {
      // Restore previous session
      EigenTerminal.print('— Session restored —', 'system');
      EigenTerminal.renderHistory(data.messages);
    } else {
      // Fresh session — play boot sequence
      if (typeof EigenAnimations !== 'undefined' && EigenAnimations.playBoot) {
        await EigenAnimations.playBoot();
      } else {
        EigenTerminal.print('EIGENFORM online. At your service, sir.', 'system');
      }
    }
  }

  /** Handle a submitted message (text or voice). */
  async function submitMessage(message) {
    if (!message || !message.trim()) return;
    if (window.EIGENFORM.isStreaming) return;

    const text = message.trim();

    // Check for client-side commands first
    if (EigenParser.handle(text)) {
      return;
    }

    // Add to command history
    EigenHistory.push(text);

    // Render user line
    EigenTerminal.print(text, 'user');

    // Open a Rocky streaming line
    EigenTerminal.startStreaming();
    window.EIGENFORM.mode = 'thinking';

    // Start TTS accumulator if available (Phase 2)
    if (typeof EigenSynthesis !== 'undefined' && EigenSynthesis.beginAccumulating) {
      EigenSynthesis.beginAccumulating();
    }

    await EigenClient.streamChat(text, {
      onToken(token) {
        EigenTerminal.appendToken(token);
        // Feed token to TTS accumulator (Phase 2)
        if (typeof EigenSynthesis !== 'undefined' && EigenSynthesis.feedToken) {
          EigenSynthesis.feedToken(token);
        }
      },

      onDone() {
        EigenTerminal.finalizeStreaming();
        window.EIGENFORM.mode = 'idle';
        // Flush remaining TTS buffer (Phase 2)
        if (typeof EigenSynthesis !== 'undefined' && EigenSynthesis.flush) {
          EigenSynthesis.flush();
        }
      },

      onError(event) {
        EigenTerminal.finalizeStreaming();
        EigenTerminal.print(event.message || 'An error occurred.', 'error');
        window.EIGENFORM.mode = 'idle';
        // Update HUD status ring to red
        if (typeof EigenHUD !== 'undefined') EigenHUD.setStatus('offline');
      },

      onInterrupted() {
        EigenTerminal.markInterrupted();
        window.EIGENFORM.mode = 'idle';
        EigenTerminal.print('Stopped.', 'rocky');
        if (typeof EigenSynthesis !== 'undefined' && EigenSynthesis.speak) {
          EigenSynthesis.speak('Stopped.');
        }
      },
    });
  }

  /** Wire all UI event listeners. */
  function _bindEvents() {
    const input       = document.getElementById('terminalInput');
    const interruptBtn = document.getElementById('interruptBtn');
    const muteBtn     = document.getElementById('muteBtn');

    // Submit on Enter
    input.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const text = input.value;
        input.value = '';
        window.EIGENFORM.historyIndex = -1;
        await submitMessage(text);
        return;
      }
      // Arrow key history navigation
      EigenHistory.handleKey(e);
    });

    // STOP button
    interruptBtn.addEventListener('click', async () => {
      if (window.EIGENFORM.isStreaming || window.EIGENFORM.isSpeaking) {
        if (typeof EigenSynthesis !== 'undefined') EigenSynthesis.cancel();
        await EigenClient.interrupt();
      }
    });

    // Escape key — interrupt
    document.addEventListener('keydown', async (e) => {
      if (e.key === 'Escape') {
        if (window.EIGENFORM.isStreaming || window.EIGENFORM.isSpeaking) {
          if (typeof EigenSynthesis !== 'undefined') EigenSynthesis.cancel();
          await EigenClient.interrupt();
        }
      }
    });

    // Mute button (also handled by /mute command)
    muteBtn.addEventListener('click', () => {
      EigenParser.handle('/mute');
    });

    // T key — cycle theme (when not typing)
    document.addEventListener('keydown', (e) => {
      if (e.key === 't' || e.key === 'T') {
        if (document.activeElement !== input) {
          if (typeof EigenThemes !== 'undefined') EigenThemes.cycle();
        }
      }
    });
  }

  /** Public boot function — called by main.js */
  async function boot() {
    _initSessionId();
    _bindEvents();

    // Start HUD (clock + status polling)
    if (typeof EigenHUD !== 'undefined') EigenHUD.start();

    // Init voice synthesis stub (Phase 2 fills this in)
    if (typeof EigenSynthesis !== 'undefined' && EigenSynthesis.init) {
      EigenSynthesis.init();
    }

    // Init STT stub (Phase 2 fills this in)
    if (typeof EigenSpeech !== 'undefined' && EigenSpeech.init) {
      EigenSpeech.init();
    }

    // Init visualizer stub (Phase 6 fills this in)
    if (typeof EigenVisualizer !== 'undefined' && EigenVisualizer.init) {
      EigenVisualizer.init();
    }

    // Init theme switcher
    if (typeof EigenThemes !== 'undefined') EigenThemes.init();

    // Restore session or play boot sequence
    await _restoreOrBoot();

    // Focus the input
    document.getElementById('terminalInput')?.focus();
  }

  return { boot, submitMessage };
})();
