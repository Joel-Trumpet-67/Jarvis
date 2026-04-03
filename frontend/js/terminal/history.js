/**
 * history.js — Command history navigation.
 *
 * Stores every submitted command. Up/Down arrow keys navigate through it.
 * Attached to the terminal input element by app.js.
 *
 * Exposed as: EigenHistory
 *   .push(command)    — add a command to history
 *   .handleKey(event) — bind this to 'keydown' on the input element
 */

const EigenHistory = (() => {
  const MAX_HISTORY = 100;

  // history is stored on the global state object
  function _history() { return window.EIGENFORM.commandHistory; }

  /** Add a command to history. Deduplicates consecutive duplicates. */
  function push(command) {
    const h = _history();
    if (!command.trim()) return;
    if (h.length > 0 && h[h.length - 1] === command) return;

    h.push(command);
    if (h.length > MAX_HISTORY) h.shift();

    // Reset navigation index after new entry
    window.EIGENFORM.historyIndex = -1;
  }

  /**
   * Handle Up/Down arrow key presses on the input element.
   * @param {KeyboardEvent} event
   */
  function handleKey(event) {
    const input = event.target;
    const h     = _history();
    if (!h.length) return;

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      let idx = window.EIGENFORM.historyIndex;
      idx = idx < h.length - 1 ? idx + 1 : idx;
      window.EIGENFORM.historyIndex = idx;
      input.value = h[h.length - 1 - idx] || '';
      // Move cursor to end
      setTimeout(() => input.setSelectionRange(input.value.length, input.value.length), 0);
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      let idx = window.EIGENFORM.historyIndex;
      if (idx <= 0) {
        window.EIGENFORM.historyIndex = -1;
        input.value = '';
        return;
      }
      idx -= 1;
      window.EIGENFORM.historyIndex = idx;
      input.value = idx >= 0 ? h[h.length - 1 - idx] : '';
    }
  }

  return { push, handleKey };
})();
