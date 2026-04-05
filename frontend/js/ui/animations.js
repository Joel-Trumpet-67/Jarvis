/**
 * animations.js — Boot sequence and UI transitions.
 *
 * Phase 1: Simple text-based boot sequence (fully working).
 * Phase 6: Full animated boot overlay with logo, scanlines, timing chains.
 *
 * Exposed as: EigenAnimations
 */

const EigenAnimations = (() => {

  const BOOT_LINES = [
    '// EIGENFORM v1.0 — Initializing...',
    '// Loading personality matrix......... OK',
    '// Connecting to AI core.............. OK',
    '// Memory subsystems.................. READY',
    '// Voice interface.................... STANDBY',
    '// All systems nominal.',
    '',
    'Online. Ready.',
  ];

  const BOOT_LINE_DELAY_MS = 160;

  /** Sleep helper */
  function _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Play the boot sequence — prints lines one at a time.
   * Returns a Promise that resolves when complete.
   */
  async function playBoot() {
    for (const line of BOOT_LINES) {
      if (!line) {
        await _sleep(BOOT_LINE_DELAY_MS / 2);
        continue;
      }
      const type = line.startsWith('//') ? 'system' : 'rocky';
      EigenTerminal.print(line, type);
      await _sleep(BOOT_LINE_DELAY_MS);
    }
  }

  return { playBoot };
})();
