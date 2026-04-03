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
  async function streamChat(message, callbacks = {}) {
    const { onToken, onDone, onError, onInterrupted } = callbacks;

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
