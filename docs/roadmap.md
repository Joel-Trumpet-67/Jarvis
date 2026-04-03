# EIGENFORM — Implementation Roadmap
**Last Updated:** 2026-04-02
**Based on:** spec.md v2.0

---

## How to Read This Document

- **Difficulty** is rated 1–5 stars (★) — 1 = straightforward, 5 = genuinely hard
- **Dependencies** lists what MUST be complete before this task can start
- **Milestone** marks a testable checkpoint where the system visibly works
- Tasks within a phase can be done in order listed — earlier tasks unblock later ones

---

## Phase 1 — Skeleton: Get It Talking

**Goal:** Type a message in the browser, receive a streamed Jarvis response. No voice, no apps. Just the core loop working end-to-end.

**Estimated time:** 1–2 days

---

### Task 1.1 — `data/config/settings.json`
**Difficulty:** ★☆☆☆☆
**Depends on:** Nothing
**What you're doing:** Create the master config file. All other files read from this.
**Risk:** None. It's a JSON file.
**Notes:** Fill in your actual model API URL and model name here first. Everything downstream assumes this exists.

---

### Task 1.2 — `backend/config.py`
**Difficulty:** ★☆☆☆☆
**Depends on:** 1.1
**What you're doing:** Python module that loads `settings.json` and exposes a `CONFIG` dict. Every other backend file imports from here instead of reading the JSON directly.
**Risk:** None.
**Notes:** Add a guard that prints a clear error if `settings.json` is missing or malformed — this will save debugging time later.

---

### Task 1.3 — `backend/ai/personality/jarvis.py`
**Difficulty:** ★☆☆☆☆
**Depends on:** 1.2
**What you're doing:** A Python file that returns the Jarvis system prompt string. Reads `user_name` from CONFIG.
**Risk:** None. This is just a string.
**Notes:** This is the most important string in the entire project. Take time to write it well. A good system prompt shapes everything Jarvis says.

---

### Task 1.4 — `backend/ai/personality/responses.py`
**Difficulty:** ★☆☆☆☆
**Depends on:** 1.2
**What you're doing:** Lists of canned strings — boot messages, error quips, idle phrases. Exported as Python lists, randomly selected at runtime.
**Risk:** None.

---

### Task 1.5 — `backend/ai/memory/short_term.py`
**Difficulty:** ★★☆☆☆
**Depends on:** 1.2
**What you're doing:** A `SessionState` class holding a thread-safe message list and a `cancel_requested` flag. Keyed by `session_id` in a module-level dict.
**Risk:** Low. The thread locking is simple but must be correct — lock before read AND write.
**Notes:** This is shared state accessed by multiple routes. Get the locking right here or debugging it later will be painful.

---

### Task 1.6 — `backend/ai/core/engine.py`
**Difficulty:** ★★★☆☆
**Depends on:** 1.2, 1.3, 1.5
**What you're doing:** The function that calls your AI model API with `stream=True`, yields tokens one by one, and checks `cancel_requested` on every yield.
**Risk:** Medium. Streaming HTTP responses in Python require careful handling — `requests` with `stream=True` and iterating `response.iter_content()`. If your model API format is different (e.g., Ollama vs OpenAI), the token extraction logic changes.
**Notes:** Test this in isolation first with a simple Python script before wiring it to Flask. Confirm your model API actually supports streaming and what the response format looks like.

---

### Task 1.7 — `backend/api/routes/chat.py`
**Difficulty:** ★★★☆☆
**Depends on:** 1.5, 1.6
**What you're doing:** The Flask SSE route. Calls engine.py, wraps tokens in SSE format (`data: {...}\n\n`), yields them to the browser.
**Risk:** Medium. SSE in Flask requires the right response headers and `threaded=True`. Easy to get a response that looks right but buffered by Flask or the browser.
**Notes:** The `X-Accel-Buffering: no` header is critical — without it, Nginx/proxies buffer your stream. For localhost it's fine, but add it anyway for correctness.

---

### Task 1.8 — `backend/api/routes/status.py`
**Difficulty:** ★☆☆☆☆
**Depends on:** 1.2, 1.5
**What you're doing:** `GET /api/status` — pings the model API, returns JSON with health info. Used by the frontend HUD.
**Risk:** None.

---

### Task 1.9 — `backend/api/routes/session.py`
**Difficulty:** ★★☆☆☆
**Depends on:** 1.5
**What you're doing:** `GET /api/session` returns conversation history. `DELETE /api/session` clears it.
**Risk:** Low.

---

### Task 1.10 — `backend/main.py`
**Difficulty:** ★★☆☆☆
**Depends on:** 1.7, 1.8, 1.9
**What you're doing:** Flask app factory. Registers all routes, sets CORS, runs with `threaded=True` on the configured host/port.
**Risk:** Low. Common Flask setup.
**Notes:** Add a startup message that prints the model URL and confirms settings loaded correctly. Makes it much easier to spot misconfiguration.

---

### Task 1.11 — `frontend/index.html`
**Difficulty:** ★☆☆☆☆
**Depends on:** Nothing (can be written in parallel with backend)
**What you're doing:** The HTML shell. One `<div id="terminal">`, one `<input>`, links to all CSS and JS files.
**Risk:** None.

---

### Task 1.12 — `frontend/css/main.css` + `terminal.css`
**Difficulty:** ★★☆☆☆
**Depends on:** 1.11
**What you're doing:** Base styles — color variables, font, layout. Terminal window with scrollable output and sticky input at bottom.
**Risk:** Low. CSS scrollbar behavior can be fiddly across browsers.
**Notes:** Define all colors as CSS custom properties (`--text-jarvis` etc.) in `main.css`. This makes theming changes instant across the whole app.

---

### Task 1.13 — `frontend/js/core/state.js`
**Difficulty:** ★☆☆☆☆
**Depends on:** Nothing
**What you're doing:** A single global `window.EIGENFORM` state object. Holds: `isListening`, `isSpeaking`, `isMuted`, `sessionId`, `commandHistory`.
**Risk:** None.
**Notes:** Keep this a plain JS object. No framework needed. Every other module reads/writes to this object.

---

### Task 1.14 — `frontend/js/api/client.js`
**Difficulty:** ★★★☆☆
**Depends on:** 1.13
**What you're doing:** Wrapper around `fetch()` and `EventSource`. Exposes `streamChat(message, onToken, onDone, onError)` and `interrupt()`. Manages the `AbortController`.
**Risk:** Medium. EventSource doesn't natively support POST bodies — you'll use `fetch()` with `ReadableStream` instead of `EventSource` for the streaming chat call. This is slightly more complex than basic `EventSource`.
**Notes:** This is the most technically tricky frontend file. The pattern is: `fetch('/api/chat', {method: 'POST', body: ...})` then read `response.body` as a `ReadableStream`, split on `\n\n`, parse SSE events manually.

---

### Task 1.15 — `frontend/js/terminal/terminal.js`
**Difficulty:** ★★☆☆☆
**Depends on:** 1.13
**What you're doing:** Functions to append lines to the terminal DOM. Line types: `user`, `jarvis`, `system`, `error`. Handles streaming token append (finds the active Jarvis line and appends to it).
**Risk:** Low. DOM manipulation.
**Notes:** Auto-scroll to bottom on every new line/token. This is easy to forget and annoying when missing.

---

### Task 1.16 — `frontend/js/main.js` + `frontend/js/core/app.js`
**Difficulty:** ★★☆☆☆
**Depends on:** 1.13, 1.14, 1.15
**What you're doing:** `main.js` is the entry point — runs on `DOMContentLoaded`. `app.js` handles startup: fetches session history, renders it, sets up the input submit handler.
**Risk:** Low.

---

### ✅ MILESTONE 1 — Core Loop Working
**Test:** Open browser → type a message → Jarvis streams a response token by token → terminal displays it.
**Pass criteria:**
- Tokens arrive and append in real time (not all at once)
- Jarvis sounds like Jarvis (personality prompt working)
- `/api/status` returns `{"model_reachable": true}`
- Refreshing the page restores conversation history

---

## Phase 2 — Voice

**Goal:** Speak to Jarvis using the wake word. Hear it respond out loud.

**Estimated time:** 1 day

---

### Task 2.1 — `frontend/js/voice/speech.js`
**Difficulty:** ★★★★☆
**Depends on:** Milestone 1, 1.13, 1.14
**What you're doing:** Implements the wake word + STT state machine. Always-on recognition listening for "hey jarvis". On detection: switches to active listening, shows interim ghost text, submits on final result.
**Risk:** High. Web Speech API is browser-specific (Chrome/Edge only), behavior varies, and the interim/final event timing is inconsistent. The echo suppression logic (pausing STT while TTS speaks) requires careful coordination with synthesis.js.
**Notes:** Test wake word detection in a quiet room first. The API is surprisingly sensitive. You may need to tune the wake word or use a shorter phrase. Always check `window.SpeechRecognition || window.webkitSpeechRecognition` for browser support and show a warning if absent.

---

### Task 2.2 — `frontend/js/voice/synthesis.js`
**Difficulty:** ★★★☆☆
**Depends on:** Milestone 1, 1.13
**What you're doing:** Sentence accumulator. Receives tokens from terminal.js, buffers them, dispatches `SpeechSynthesisUtterance` on sentence boundaries. Manages utterance queue. Handles cancel on interrupt.
**Risk:** Medium. `SpeechSynthesis` has a known Chrome bug where it stops speaking after ~15 seconds on long responses. The fix is to pause/resume it periodically. The sentence boundary detection regex needs the abbreviation exception list.
**Notes:** `window.speechSynthesis.getVoices()` returns an empty array until the `voiceschanged` event fires. Wait for that event before selecting the en-GB voice.

---

### Task 2.3 — `frontend/js/terminal/history.js`
**Difficulty:** ★☆☆☆☆
**Depends on:** 1.13, 1.15
**What you're doing:** Stores submitted commands in an array. Up/down arrow keys navigate through history and fill the input box.
**Risk:** None.

---

### ✅ MILESTONE 2 — Full Voice Loop Working
**Test:** Say "Hey Jarvis" → speak a question → Jarvis responds by voice while printing to terminal.
**Pass criteria:**
- Wake word reliably activates STT
- Interim text appears as grey ghost in input box
- Final transcript submitted and responded to
- TTS speaks in en-GB at correct rate/pitch
- STT pauses while TTS is speaking (no echo loop)

---

## Phase 3 — Interrupt + Session Resilience

**Goal:** Escape stops everything. Browser refresh restores the session perfectly.

**Estimated time:** Half a day

---

### Task 3.1 — Interrupt: Backend cancel token
**Difficulty:** ★★☆☆☆
**Depends on:** Milestone 1, 1.5, 1.7
**What you're doing:** Add `POST /api/interrupt` route. Sets `session.cancel_requested = True`. Add cancel check inside `engine.py` stream generator.
**Risk:** Low. The lock is already in place from Task 1.5.

---

### Task 3.2 — Interrupt: Frontend AbortController + TTS cancel
**Difficulty:** ★★☆☆☆
**Depends on:** 3.1, 2.2
**What you're doing:** Wire Escape key and interrupt button to: `speechSynthesis.cancel()`, abort the fetch stream, POST `/api/interrupt`, print "Of course, sir." in terminal and speak it.
**Risk:** Low.

---

### Task 3.3 — Session restore on page load
**Difficulty:** ★★☆☆☆
**Depends on:** Milestone 1, 1.9, 1.15, 1.16
**What you're doing:** In `app.js` boot, call `GET /api/session`. If messages exist, render them all with `terminal.renderHistory()`. If empty, play boot animation.
**Risk:** Low.

---

### ✅ MILESTONE 3 — Resilient Session
**Test:** Jarvis is mid-response → press Escape → everything stops → "Of course, sir." → refresh page → conversation history re-appears.

---

## Phase 4 — App Launcher + Dispatcher

**Goal:** "Open Chrome" actually opens Chrome. Dispatcher routes correctly.

**Estimated time:** 2 days

---

### Task 4.1 — `data/apps/app_registry.json`
**Difficulty:** ★☆☆☆☆
**Depends on:** Nothing
**What you're doing:** Fill in your actual application paths. Test each path manually first.
**Risk:** None. Just a JSON file, but wrong paths silently fail.
**Notes:** Use full absolute paths. Test each one works by running it directly in Python before adding to the registry.

---

### Task 4.2 — `backend/ai/nlp/parser.py` + `intent.py` + `entities.py`
**Difficulty:** ★★★☆☆
**Depends on:** 1.2
**What you're doing:**
- `parser.py`: lowercase, strip, normalize unicode
- `intent.py`: score input against registered keyword patterns, return confidence map
- `entities.py`: extract app name, time references, quantities from normalized text
**Risk:** Medium. Entity extraction without an ML model is regex-based and will have gaps. Fuzzy app name matching needs thought — use `difflib.get_close_matches()` for simple fuzzy matching without extra libraries.
**Notes:** Keep a unit test list of inputs and expected intents. You'll be adding to this list constantly as edge cases appear.

---

### Task 4.3 — `backend/ai/core/registry.py`
**Difficulty:** ★★☆☆☆
**Depends on:** 1.2
**What you're doing:** Module-level dict that stores registered plugin schemas. `register(plugin_dict)` adds to it. `get_all()` returns the full list. `query(intent_name)` returns the handler for a given intent.
**Risk:** Low. This is a dict wrapper.

---

### Task 4.4 — `backend/systems/__init__.py`
**Difficulty:** ★★★☆☆
**Depends on:** 4.3
**What you're doing:** Auto-discover all `plugin.py` files in `systems/` subdirectories using `importlib` and `pkgutil`. Call `register()` on each. Called once at Flask startup.
**Risk:** Medium. Python dynamic imports with `importlib` can be confusing. The pattern is straightforward but needs to be right.
**Notes:** Add a startup print statement listing all registered plugins. Makes it obvious when a plugin fails to load.

---

### Task 4.5 — `backend/systems/apps/launcher.py` + `registry.py` + `plugin.py`
**Difficulty:** ★★☆☆☆
**Depends on:** 4.3, 4.4, 4.1
**What you're doing:**
- `registry.py`: loads `app_registry.json`, resolves aliases, fuzzy-matches app names
- `launcher.py`: whitelist-only `subprocess.Popen` with `shell=False`
- `plugin.py`: `register()` returning intent patterns and handler
**Risk:** Low.
**Notes:** `shell=False` is non-negotiable. Never use `shell=True` here.

---

### Task 4.6 — `backend/ai/core/dispatcher.py`
**Difficulty:** ★★★★☆
**Depends on:** 4.2, 4.3, 1.6
**What you're doing:** The hybrid router. Runs keyword scoring → if confidence ≥ 0.80, routes to plugin handler. If not, calls AI model to classify intent, routes to that handler. Falls back to `engine.py` conversation if no intent matches.
**Risk:** High. This is the most complex backend file. The interaction between the confidence threshold, the AI classification call, the plugin registry query, and the fallback to conversation all need to work correctly together. Bugs here affect every single request.
**Notes:** Add verbose logging in development mode — log the confidence map for every request. You will need this to tune the threshold and debug misroutes. Test with a wide variety of phrasings before considering it done.

---

### ✅ MILESTONE 4 — App Control Working
**Test:** "Hey Jarvis, open Notepad" → Notepad opens → Jarvis confirms. "Hey Jarvis, what's 2 + 2?" → Jarvis answers conversationally (not tries to open an app).
**Pass criteria:**
- Registered apps launch on voice/text command
- Unregistered apps get an elegant refusal
- Conversational questions still route to AI correctly
- No false positives (asking about a movie doesn't open an app)

---

## Phase 5 — Long-Term Memory

**Goal:** Jarvis remembers facts you tell it across sessions.

**Estimated time:** 1 day

---

### Task 5.1 — `backend/ai/memory/long_term.py`
**Difficulty:** ★★★☆☆
**Depends on:** 1.2
**What you're doing:** Thread-safe JSON read/write with `threading.Lock`. Atomic writes via temp file + `os.replace()`. Backup before every write. `JSONDecodeError` recovery.
**Risk:** Medium. The locking and atomic write pattern needs to be exactly right. A wrong implementation here means either corrupted files or deadlocks.
**Notes:** Test corruption recovery explicitly — manually break `long_term.json` and confirm the system recovers gracefully.

---

### Task 5.2 — `backend/ai/memory/context.py`
**Difficulty:** ★★★☆☆
**Depends on:** 5.1, 1.5, 1.3
**What you're doing:** Assembles the full context window for the model. Extracts keywords from the current message, scores long-term memory entries by tag overlap, injects top 5 relevant memories, adds short-term history. Enforces token budget.
**Risk:** Medium. Token counting without a tokenizer library is approximate — use word count × 1.3 as a rough estimate. Good enough for budget enforcement.

---

### Task 5.3 — `backend/api/routes/memory.py`
**Difficulty:** ★☆☆☆☆
**Depends on:** 5.1
**What you're doing:** `GET /api/memory` and `DELETE /api/memory` routes.
**Risk:** None.

---

### ✅ MILESTONE 5 — Memory Working
**Test:** Tell Jarvis "Remember that I prefer dark mode." Restart Flask. Ask "Do you remember my display preferences?" → Jarvis knows.
**Pass criteria:**
- Fact stored in `long_term.json` with correct tags
- Fact retrieved and injected in next session
- `/memory` client command shows stored facts
- Corrupt JSON is recovered without crash

---

## Phase 6 — HUD & Polish

**Goal:** It looks like Iron Man. Boot animation, scanlines, HUD elements, audio visualizer.

**Estimated time:** 2–3 days

---

### Task 6.1 — `frontend/css/hud.css` + `animations.css`
**Difficulty:** ★★★☆☆
**Depends on:** Milestone 1
**What you're doing:**
- HUD corner panels, status ring, bottom bar
- Boot sequence keyframes
- Scanline CSS overlay
- Glow effects on input and Jarvis lines
- Typing cursor animation
**Risk:** Medium. CSS animations are easy to write badly — jank, repaints, layout thrash. Use `transform` and `opacity` only for animations (GPU composited). Avoid animating `width`, `height`, `top`, `left`.

---

### Task 6.2 — `frontend/js/ui/hud.js`
**Difficulty:** ★★☆☆☆
**Depends on:** 6.1, 1.13
**What you're doing:** Live clock (updates every second), connection status indicator (polls `/api/status` every 30s, changes ring color), voice mode indicator.
**Risk:** Low.
**Notes:** The clock runs in JS, NOT by polling the backend. `setInterval` with `new Date()`.

---

### Task 6.3 — `frontend/js/ui/visualizer.js`
**Difficulty:** ★★★☆☆
**Depends on:** 2.1
**What you're doing:** Canvas 2D bar visualizer that activates during voice input. Uses `getUserMedia` + `AudioContext` + `AnalyserNode` to read mic amplitude and draw frequency bars.
**Risk:** Medium. Web Audio API is straightforward once you know the pattern, but the first time is confusing. The bars should only show during active STT listening, not during TTS.

---

### Task 6.4 — `frontend/js/ui/animations.js`
**Difficulty:** ★★★☆☆
**Depends on:** 6.1
**What you're doing:** Boot sequence — timed series of system messages with delays, logo reveal, then transition to normal terminal. Typing effect (character-by-character append). Transition effects between states.
**Risk:** Medium. Timing chains with `setTimeout` can get messy. Use `async/await` with a `sleep(ms)` helper function to keep the boot sequence readable.

---

### Task 6.5 — `frontend/js/terminal/parser.js`
**Difficulty:** ★☆☆☆☆
**Depends on:** Milestone 1, 1.15, 5.3
**What you're doing:** Intercepts `/command` inputs before they're sent to the API. Handles `/help`, `/clear`, `/mute`, `/memory`, `/status`, `/boot`, `/history`.
**Risk:** None.

---

### ✅ MILESTONE 6 — Full Jarvis Experience
**Test:** Cold-start the app → boot animation plays → HUD shows clock and status → say "Hey Jarvis" → visualizer activates → response streams with typing effect → scanlines visible throughout.
**Pass criteria:**
- Boot animation plays on fresh load
- All HUD elements present and live
- Audio visualizer responds to voice
- Scanlines and glow effects visible
- All `/commands` work

---

## Phase 7 — Expansion Subsystems

**Goal:** OS control, web search, multi-step task planning.

**Estimated time:** 3–5 days (ongoing)

> Each subsystem in Phase 7 is independent. Do them in any order.

---

### Task 7.1 — OS Control (`systems/os_control/`)
**Difficulty:** ★★★☆☆
**Depends on:** Milestone 4
**What you're doing:** Volume control (`pycaw` or `pyautogui`), brightness (`screen-brightness-control`), window focus (`pywin32`). Each wrapped in a plugin that registers with the dispatcher.
**Risk:** Medium. Windows API calls vary by version. Some require admin privileges. Test each capability standalone before integrating.
**New packages:** `pycaw`, `screen-brightness-control`, `pywin32`

---

### Task 7.2 — Web Search (`systems/web/`)
**Difficulty:** ★★☆☆☆
**Depends on:** Milestone 4
**What you're doing:** Use DuckDuckGo Instant Answer API (free, no key) or a search scraper. Return top 3 results as text. Jarvis summarizes them.
**Risk:** Low. Web scraping can break if the target site changes HTML.
**Notes:** DuckDuckGo Instant Answer API: `https://api.duckduckgo.com/?q={query}&format=json` — returns structured data for many queries without scraping.

---

### Task 7.3 — Task Planner (`ai/reasoning/planner.py`)
**Difficulty:** ★★★★☆
**Depends on:** Milestone 4, 5
**What you're doing:** For multi-step commands ("Open Spotify, turn volume to 50%, then search for Led Zeppelin"), the planner breaks the input into an ordered list of atomic tasks and executes them sequentially through the dispatcher.
**Risk:** High. Multi-step parsing with natural language is hard without ML. Start with conjunctions ("and then", "then", "after that") as split markers. True multi-step planning (understanding implicit dependencies) requires the AI model as the planner.

---

### Task 7.4 — File Manager (`systems/files/`)
**Difficulty:** ★★★☆☆
**Depends on:** Milestone 4
**What you're doing:** Sandboxed file read and search within `allowed_dirs`. Path traversal prevention via `os.path.realpath()`. Never write files unless explicitly added later.
**Risk:** Medium. Security-critical. The sandbox logic must be tested with adversarial paths (`../../`, symlinks, etc.).

---

### ✅ MILESTONE 7 — Fully Expanded Jarvis
**Test:** "Hey Jarvis, search for the latest news on AI, turn the volume down to 30%, then open Chrome."
**Pass criteria:**
- Each step executes in order
- OS commands take effect
- Web search returns summarized results
- File operations stay within allowed directories

---

## Dependency Graph Summary

```
1.1 settings.json
 └─ 1.2 config.py
     ├─ 1.3 jarvis.py
     ├─ 1.4 responses.py
     ├─ 1.5 short_term.py ──────────────────────────────┐
     │   └─ 1.6 engine.py                                │
     │       └─ 1.7 chat.py ──┐                          │
     ├─ 1.8 status.py         │                          │
     └─ 1.9 session.py        │                          │
                              │                          │
         1.10 main.py ◄───────┘                          │
                                                         │
         1.11-1.16 Frontend ◄─── MILESTONE 1 ───────────┘
              │
         2.1 speech.js
         2.2 synthesis.js ──── MILESTONE 2
              │
         3.1 interrupt backend
         3.2 interrupt frontend ─── MILESTONE 3
              │
         4.2 nlp/ ─── 4.3 registry ─── 4.4 systems/__init__
                                              │
                                        4.5 apps/plugin
                                              │
                                        4.6 dispatcher ─── MILESTONE 4
                                              │
                                   5.1 long_term
                                   5.2 context
                                   5.3 memory routes ─── MILESTONE 5
                                              │
                                   6.1-6.5 HUD & Polish ─── MILESTONE 6
                                              │
                                   7.x Expansion ─── MILESTONE 7
```

---

## Difficulty Summary

| Phase | Hardest Task | Why |
|-------|-------------|-----|
| 1 | `client.js` (fetch ReadableStream) | SSE via fetch is non-obvious |
| 2 | `speech.js` (STT state machine) | Web Speech API is flaky and browser-specific |
| 3 | None — mostly wiring | Simple coordination work |
| 4 | `dispatcher.py` (hybrid router) | Most logic, most edge cases, most impact |
| 5 | `long_term.py` (atomic locks) | Must be exactly right or data corrupts |
| 6 | `animations.js` (boot sequence) | Timing chains, polish is hard |
| 7 | `planner.py` (task chaining) | NLP without ML is fundamentally limited |

---

*Build in order. Test each milestone before moving on. Don't skip ahead.*
