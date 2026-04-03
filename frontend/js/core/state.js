/**
 * state.js — Global application state.
 *
 * A single plain object on window.EIGENFORM.
 * Every other module reads and writes to this.
 * Loaded first — before any other script.
 */

window.EIGENFORM = {
  // Backend URL — change this if Flask runs on a different port
  API_BASE: 'http://127.0.0.1:5000',

  // Session identity
  sessionId: null,

  // Current operating mode
  // Possible values: 'idle' | 'listening' | 'thinking' | 'speaking'
  mode: 'idle',

  // Voice flags
  isMuted:     false,   // TTS muted
  isListening: false,   // STT mic is active
  isSpeaking:  false,   // TTS is currently playing

  // Active fetch AbortController (for interrupt)
  currentAbortController: null,

  // Whether a response is currently streaming
  isStreaming: false,

  // Command history (for arrow-key navigation)
  commandHistory:  [],
  historyIndex:    -1,

  // Model connection status
  modelOnline: false,
};
