/**
 * client.js — All HTTP communication with the Flask backend.
 *
 * Uses fetch() + ReadableStream to handle SSE streaming responses.
 * (We use fetch instead of EventSource because EventSource only supports GET,
 *  but our chat endpoint is POST.)
 *
 * Exposed functions:
 *   EigenClient.streamChat(message, callbacks)
 *   EigenClient.interrupt()
 *   EigenClient.getSession()
 *   EigenClient.clearSession()
 *   EigenClient.getStatus()
 */

const EigenClient = (() => {
  const base = () => window.EIGENFORM.API_BASE;
  const sessionId = () => window.EIGENFORM.sessionId || 'default';

  const defaultHeaders = () => ({
    'Content-Type':  'application/json',
    'X-Session-ID':  sessionId(),
  });

  /**
   * streamChat — POST /api/chat with SSE streaming.
   *
   * @param {string} message
   * @param {object} callbacks
   *   .onToken(token)       — called for each streamed token
   *   .onDone()             — called when stream completes normally
   *   .onError(event)       — called on model error {code, message}
   *   .onInterrupted()      — called when stream was cancelled
   */
  /**
   * _tryCommand — Check if the message is a local computer command.
   * If it matches, execute it and call onToken/onDone directly.
   * Returns true if handled, false if the message should go to the AI.
   */
  function _tryCommand(message, callbacks) {
    const { onToken, onDone } = callbacks;
    const msg = message.toLowerCase().trim();

    // Scene triggers — pass through to backend (backend owns scenes)
    const scenePatterns = [
      /wake\s+up\s+daddy.?s\s+home/i,
      /daddy.?s\s+home/i,
      /i.?m\s+home/i,
      /work\s+mode/i,
      /time\s+to\s+work/i,
    ];
    if (scenePatterns.some(p => p.test(message))) return false;

    // YouTube: play / search
    const ytPlay = /\b(?:play|stream|watch|search|find|put on)\b.{0,60}\b(?:youtube|yt)\b/i.test(message)
                || /\b(?:youtube|yt)\b.{0,60}\b(?:play|search|find|watch)\b/i.test(message);

    if (ytPlay) {
      let query = null;
      const patterns = [
        /\bplay\s+(.+?)\s+on\s+(?:youtube|yt)/i,
        /\bplay\s+(.+?)\s+(?:youtube|yt)/i,
        /\bwatch\s+(.+?)\s+on\s+(?:youtube|yt)/i,
        /\bstream\s+(.+?)\s+on\s+(?:youtube|yt)/i,
        /\bsearch\s+(?:for\s+)?(.+?)\s+on\s+(?:youtube|yt)/i,
        /\b(?:youtube|yt)\b[,\s]+(?:play|search\s+for|find)\s+(.+)/i,
      ];
      for (const pat of patterns) {
        const m = message.match(pat);
        if (m && m[1].trim()) { query = m[1].trim(); break; }
      }

      const url = query
        ? `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`
        : 'https://www.youtube.com';
      const reply = query ? `Opening YouTube — ${query}.` : 'Opening YouTube.';

      window.open(url, '_blank');
      if (onToken) onToken(reply);
      if (onDone)  onDone();
      return true;
    }

    // Open YouTube homepage
    if (/\b(?:open|launch|go\s+to)\s+(?:youtube|yt)\b/i.test(message)) {
      window.open('https://www.youtube.com', '_blank');
      if (onToken) onToken('Opening YouTube.');
      if (onDone)  onDone();
      return true;
    }

    // Spotify: open playlist in desktop app
    if (/\b(?:play|open|launch|start)\b.{0,30}\b(?:my\s+)?playlist\b/i.test(message)
     || /\b(?:open|launch)\s+spotify\b/i.test(message)) {
      window.open('spotify:playlist:4K92J71PPuxqvq8l8Q2tlO', '_blank');
      if (onToken) onToken('Opening your playlist.');
      if (onDone)  onDone();
      return true;
    }

    // Web search: "google X", "search for X", "look up X", "search X"
    const webSearch =
      message.match(/\bgoogle\s+(?:for\s+)?(.+)/i) ||
      message.match(/\bsearch\s+(?:the\s+web\s+)?(?:for\s+)?(.+?)(?:\s+online)?\s*$/i) ||
      message.match(/\blook\s+up\s+(.+)/i) ||
      message.match(/\bfind\s+(?:info(?:rmation)?\s+(?:on|about)\s+)(.+)/i);

    if (webSearch) {
      const query = webSearch[1].trim();
      const url = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
      window.open(url, '_blank');
      if (onToken) onToken(`Searching — ${query}.`);
      if (onDone)  onDone();
      return true;
    }

    return false;
  }

  async function streamChat(message, callbacks = {}) {
    const { onToken, onDone, onError, onInterrupted } = callbacks;

    // Check for local commands before hitting the backend
    if (_tryCommand(message, callbacks)) return;

    // Create a new AbortController for this request
    const controller = new AbortController();
    window.EIGENFORM.currentAbortController = controller;
    window.EIGENFORM.isStreaming = true;

    try {
      const response = await fetch(`${base()}/api/chat`, {
        method:  'POST',
        headers: defaultHeaders(),
        body:    JSON.stringify({
          message,
          session_id: sessionId(),
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let   buffer  = '';

      // Read the SSE stream chunk by chunk
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE messages are separated by double newlines
        const parts = buffer.split('\n\n');
        buffer = parts.pop(); // Last part may be incomplete — keep for next chunk

        for (const part of parts) {
          const trimmed = part.trim();
          if (!trimmed.startsWith('data: ')) continue;

          let event;
          try {
            event = JSON.parse(trimmed.slice(6)); // Strip 'data: ' prefix
          } catch (_) {
            continue;
          }

          switch (event.type) {
            case 'token':
              if (onToken) onToken(event.content);
              break;
            case 'done':
              if (onDone) onDone();
              break;
            case 'error':
              if (onError) onError(event);
              break;
            case 'interrupted':
              if (onInterrupted) onInterrupted();
              break;
            case 'command_executed':
              if (callbacks.onCommandExecuted) callbacks.onCommandExecuted(event);
              break;
          }
        }
      }

    } catch (err) {
      if (err.name === 'AbortError') {
        // Expected — user triggered interrupt. Do nothing here.
        return;
      }
      if (onError) {
        onError({ code: 'FETCH_ERROR', message: err.message });
      }
    } finally {
      window.EIGENFORM.isStreaming = false;
      window.EIGENFORM.currentAbortController = null;
    }
  }

  /**
   * interrupt — Abort the active stream and notify the backend.
   * Called by Escape key, STOP button, or voice interrupt phrase.
   */
  async function interrupt() {
    // 1. Abort the active fetch immediately
    if (window.EIGENFORM.currentAbortController) {
      window.EIGENFORM.currentAbortController.abort();
    }

    // 2. Notify backend to set cancel flag (for in-flight model requests)
    try {
      await fetch(`${base()}/api/interrupt`, {
        method:  'POST',
        headers: defaultHeaders(),
        body:    JSON.stringify({ session_id: sessionId() }),
      });
    } catch (_) {
      // Backend may have already closed — not critical
    }
  }

  /**
   * getSession — GET /api/session
   * Returns { session_id, messages, count }
   */
  async function getSession() {
    try {
      const r = await fetch(`${base()}/api/session`, {
        method:  'GET',
        headers: defaultHeaders(),
      });
      return await r.json();
    } catch (_) {
      return { session_id: sessionId(), messages: [], count: 0 };
    }
  }

  /**
   * clearSession — DELETE /api/session
   */
  async function clearSession() {
    try {
      await fetch(`${base()}/api/session`, {
        method:  'DELETE',
        headers: defaultHeaders(),
      });
    } catch (_) { /* ignore */ }
  }

  /**
   * getStatus — GET /api/status
   * Returns health/model info.
   */
  async function getStatus() {
    try {
      const r = await fetch(`${base()}/api/status`, {
        method:  'GET',
        headers: { 'X-Session-ID': sessionId() },
      });
      return await r.json();
    } catch (_) {
      return { model_reachable: false, status: 'offline' };
    }
  }

  return { streamChat, interrupt, getSession, clearSession, getStatus };
})();
