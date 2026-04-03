/**
 * main.js — Entry point. Loaded last.
 *
 * Waits for DOMContentLoaded then kicks off EigenApp.boot().
 * All other modules are already loaded by the time this runs.
 */

document.addEventListener('DOMContentLoaded', () => {
  EigenApp.boot().catch(err => {
    console.error('[EIGENFORM] Boot failed:', err);
    const output = document.getElementById('terminalOutput');
    if (output) {
      output.innerHTML =
        '<div class="terminal-line error">' +
        '<span class="line-prefix">!</span>' +
        '<span class="line-content">EIGENFORM failed to initialize. Check the console for details.</span>' +
        '</div>';
    }
  });
});
