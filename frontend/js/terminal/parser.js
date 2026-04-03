/**
 * parser.js — Client-side command interception.
 *
 * Checks if the input starts with '/' and handles it locally
 * without sending anything to the backend.
 *
 * Returns true if the command was handled (caller should NOT send to API).
 * Returns false if input should be forwarded to the backend.
 *
 * Exposed as: EigenParser
 *   .handle(input)  → boolean
 */

const EigenParser = (() => {

  const COMMANDS = {
    '/help':    cmdHelp,
    '/clear':   cmdClear,
    '/mute':    cmdMute,
    '/listen':  cmdListen,
    '/memory':  cmdMemory,
    '/status':  cmdStatus,
    '/boot':    cmdBoot,
    '/history': cmdHistory,
  };

  function handle(input) {
    const trimmed = input.trim();
    if (!trimmed.startsWith('/')) return false;

    const parts   = trimmed.split(/\s+/);
    const cmd     = parts[0].toLowerCase();
    const handler = COMMANDS[cmd];

    if (handler) {
      handler(parts.slice(1));
    } else {
      EigenTerminal.print(
        `Unknown command: ${cmd}. Type /help for a list of commands.`,
        'error'
      );
    }

    return true; // Command was handled — don't send to backend
  }

  // ── Command implementations ────────────────────────────────────

  function cmdHelp() {
    const lines = [
      'Available commands:',
      '  /help     — Show this list',
      '  /clear    — Clear terminal and session',
      '  /mute     — Toggle TTS on/off',
      '  /listen   — Toggle always-on microphone',
      '  /memory   — Show long-term memory contents',
      '  /status   — Show backend connection status',
      '  /boot     — Replay the boot animation',
      '  /history  — Show last 10 commands',
    ];
    lines.forEach(l => EigenTerminal.print(l, 'system'));
  }

  async function cmdClear() {
    EigenTerminal.clear();
    await EigenClient.clearSession();
    EigenTerminal.print('Session cleared.', 'system');
  }

  function cmdMute() {
    window.EIGENFORM.isMuted = !window.EIGENFORM.isMuted;
    const state = window.EIGENFORM.isMuted ? 'ON' : 'OFF';
    EigenTerminal.print(`Mute: ${state}`, 'system');
    // Update button label
    const btn = document.getElementById('muteBtn');
    if (btn) btn.textContent = `MUTE: ${state}`;
    // Stop any current speech
    if (window.EIGENFORM.isMuted && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  function cmdListen() {
    // Delegated to EigenSpeech — Phase 2
    if (typeof EigenSpeech !== 'undefined' && EigenSpeech.toggle) {
      EigenSpeech.toggle();
    } else {
      EigenTerminal.print('Voice input is not yet initialized. (Phase 2)', 'system');
    }
  }

  async function cmdMemory() {
    EigenTerminal.print('Retrieving memory...', 'system');
    try {
      const r = await fetch(`${window.EIGENFORM.API_BASE}/api/memory`, {
        headers: { 'X-Session-ID': window.EIGENFORM.sessionId || 'default' },
      });
      if (!r.ok) throw new Error('Not available yet.');
      const data = await r.json();
      const facts = data.facts || [];
      if (!facts.length) {
        EigenTerminal.print('No long-term memories stored yet.', 'system');
      } else {
        facts.forEach((f, i) => EigenTerminal.print(`  [${i + 1}] ${f.content}`, 'system'));
      }
    } catch (_) {
      EigenTerminal.print('Memory module not yet active. (Phase 5)', 'system');
    }
  }

  async function cmdStatus() {
    EigenTerminal.print('Checking system status...', 'system');
    const data = await EigenClient.getStatus();
    EigenTerminal.print(
      `Model: ${data.model_reachable ? 'ONLINE' : 'OFFLINE'} — ${data.model_name || 'unknown'} @ ${data.model_url || 'unknown'}`,
      data.model_reachable ? 'system' : 'error'
    );
    EigenTerminal.print(
      `Sessions: ${data.session_count || 0} — Messages: ${data.total_message_count || 0} — Uptime: ${data.uptime_seconds || 0}s`,
      'system'
    );
  }

  function cmdBoot() {
    if (typeof EigenAnimations !== 'undefined' && EigenAnimations.playBoot) {
      EigenAnimations.playBoot();
    } else {
      EigenTerminal.print('Boot animation not yet active. (Phase 6)', 'system');
    }
  }

  function cmdHistory() {
    const h = window.EIGENFORM.commandHistory;
    if (!h.length) {
      EigenTerminal.print('No command history yet.', 'system');
      return;
    }
    const recent = h.slice(-10).reverse();
    EigenTerminal.print('Recent commands:', 'system');
    recent.forEach((cmd, i) => EigenTerminal.print(`  ${i + 1}. ${cmd}`, 'system'));
  }

  return { handle };
})();
