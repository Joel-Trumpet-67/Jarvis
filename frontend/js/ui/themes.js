/**
 * themes.js — Theme switcher for EIGENFORM.
 *
 * Cycles through: cyan → amber → green → red → (repeat)
 * Theme is persisted in localStorage so it survives restarts.
 *
 * Exposed as: EigenThemes
 */

const EigenThemes = (() => {
  const THEMES    = ['cyan', 'amber', 'green', 'red'];
  const LABELS    = { cyan: 'CYAN', amber: 'AMBER', green: 'GREEN', red: 'RED' };
  const LS_KEY    = 'eigenform_theme';

  let _current = 0;

  // ── Apply a theme by name ────────────────────────────────────────

  function _apply(name) {
    document.documentElement.setAttribute('data-theme', name);
    _current = THEMES.indexOf(name);
    if (_current < 0) _current = 0;

    // Update the button label
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = `THEME: ${LABELS[name] || name.toUpperCase()}`;

    // Persist
    try { localStorage.setItem(LS_KEY, name); } catch (_) {}
  }

  // ── Cycle to next theme ──────────────────────────────────────────

  function cycle() {
    _current = (_current + 1) % THEMES.length;
    _apply(THEMES[_current]);
  }

  // ── Load saved theme on boot ─────────────────────────────────────

  function init() {
    let saved;
    try { saved = localStorage.getItem(LS_KEY); } catch (_) {}
    _apply(THEMES.includes(saved) ? saved : 'cyan');

    const btn = document.getElementById('themeBtn');
    if (btn) btn.addEventListener('click', cycle);
  }

  return { init, cycle, apply: _apply };
})();
