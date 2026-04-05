/**
 * terminal.js — Renders all output lines to the terminal DOM.
 *
 * Line types:  'user' | 'rocky' | 'system' | 'error' | 'interrupted'
 *
 * Exposed as: EigenTerminal
 *   .print(text, type)        — append a complete line
 *   .startStreaming()         — open a new Rocky line for token streaming
 *   .appendToken(token)       — append token to the active streaming line
 *   .finalizeStreaming()      — close the streaming line (remove cursor)
 *   .markInterrupted()        — dim the current streaming line
 *   .renderHistory(messages)  — re-render session history on page load
 *   .clear()                  — clear all output lines
 */

const EigenTerminal = (() => {
  const OUTPUT_ID  = 'terminalOutput';
  const PREFIXES   = {
    user:        '>',
    rocky:       '◈',
    system:      '//',
    error:       '!',
    interrupted: '◈',
  };

  let _activeStreamLine = null; // The current streaming Rocky line element

  function _getOutput() {
    return document.getElementById(OUTPUT_ID);
  }

  /** Scroll to the bottom of the terminal. */
  function _scrollToBottom() {
    const output = _getOutput();
    if (output) output.scrollTop = output.scrollHeight;
  }

  /**
   * Create and append a terminal line element.
   * Returns the line element so callers can hold a reference for streaming.
   */
  function _createLine(text, type = 'system') {
    const output = _getOutput();
    if (!output) return null;

    const line    = document.createElement('div');
    line.className = `terminal-line ${type}`;

    const prefix  = document.createElement('span');
    prefix.className = 'line-prefix';
    prefix.textContent = PREFIXES[type] || '·';

    const content = document.createElement('span');
    content.className = 'line-content';
    content.textContent = text;

    line.appendChild(prefix);
    line.appendChild(content);
    output.appendChild(line);

    _scrollToBottom();
    return line;
  }

  /** Print a complete, static line. */
  function print(text, type = 'system') {
    _createLine(text, type);
  }

  /**
   * Open a new Rocky line showing a thinking placeholder.
   * The placeholder is cleared automatically on the first token.
   */
  function startStreaming() {
    const line = _createLine('', 'rocky');
    if (line) {
      line.classList.add('streaming');
      _activeStreamLine = line;

      // Show thinking indicator — replaced by real content on first token
      const content = line.querySelector('.line-content');
      if (content) {
        content.dataset.thinking = 'true';
        content.textContent = 'Thinking...';
        content.style.opacity = '0.4';
        content.style.fontStyle = 'italic';
      }
    }
  }

  /** Append a token string to the active streaming line. */
  function appendToken(token) {
    if (!_activeStreamLine) return;
    const content = _activeStreamLine.querySelector('.line-content');
    if (content) {
      // Clear thinking placeholder on first real token
      if (content.dataset.thinking === 'true') {
        content.textContent = '';
        content.style.opacity = '';
        content.style.fontStyle = '';
        delete content.dataset.thinking;
      }
      content.textContent += token;
      _scrollToBottom();
    }
  }

  /** Remove the streaming cursor — response is complete. */
  function finalizeStreaming() {
    if (_activeStreamLine) {
      _activeStreamLine.classList.remove('streaming');
      _activeStreamLine = null;
    }
  }

  /** Dim the active streaming line to show it was interrupted. */
  function markInterrupted() {
    if (_activeStreamLine) {
      _activeStreamLine.classList.remove('streaming', 'rocky');
      _activeStreamLine.classList.add('interrupted');
      const prefix = _activeStreamLine.querySelector('.line-prefix');
      if (prefix) prefix.textContent = PREFIXES.interrupted;
      _activeStreamLine = null;
    }
  }

  /**
   * Re-render a full session history array on page load.
   * messages: [{role: 'user'|'assistant', content: '...', timestamp: ...}]
   */
  function renderHistory(messages) {
    if (!messages || !messages.length) return;
    messages.forEach(msg => {
      const type = msg.role === 'user' ? 'user' : 'rocky';
      print(msg.content, type);
    });
  }

  /** Clear all terminal output lines. */
  function clear() {
    const output = _getOutput();
    if (output) output.innerHTML = '';
    _activeStreamLine = null;
  }

  return {
    print,
    startStreaming,
    appendToken,
    finalizeStreaming,
    markInterrupted,
    renderHistory,
    clear,
  };
})();
