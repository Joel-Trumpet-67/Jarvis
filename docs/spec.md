# EIGENFORM — Rocky AI Assistant
## Production Specification Document

**Last Updated:** 2026-04-05
**Version:** 3.0
**Status:** Phase 1 Complete — Phase 2 In Progress

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Phase 1 — Completed](#3-phase-1--completed)
4. [Phase 2 — In Progress](#4-phase-2--in-progress)
5. [Phase 3 — Future](#5-phase-3--future)
6. [Settings Schema](#6-settings-schema)
7. [API Endpoints](#7-api-endpoints)
8. [Security Model](#8-security-model)

---

## 1. Overview

EIGENFORM is a locally-running AI assistant with a terminal-style HUD interface. It accepts text (and eventually voice) input, routes commands through a deterministic dispatcher, executes actions on the user's computer, and responds with streamed text. The AI personality is Rocky — calm, direct, capable, and efficient.

**Core principles:**
- Commands are executed deterministically. The AI model is never trusted to trigger actions.
- The system prompt and personality are enforced at the infrastructure level, not the model level.
- All capabilities are modular and register themselves at startup.
- No cloud dependencies beyond the AI model API (Groq).

**Current stack:**
- Backend: Python 3.11, Flask, requests
- Frontend: Vanilla HTML/CSS/JS (terminal UI)
- AI: Groq API — `llama-3.3-70b-versatile`
- Memory: In-process, session-scoped (no persistence yet)

---

## 2. Architecture

### Request Pipeline

```
User Input (text)
  │
  ▼
client.js: _tryCommand()          ← Frontend command interception (regex)
  │ match → execute locally (window.open), return confirmation
  │ no match ↓
  ▼
POST /api/chat (chat.py)
  │
  ▼
chat.py: _try_command()           ← Backend command interception (regex)
  │ match → execute (webbrowser.open), stream confirmation
  │ no match ↓
  ▼
dispatcher.dispatch()             ← Intent routing
  │ match → run command handler directly (no AI)
  │ no match ↓
  ▼
engine.stream_response()          ← AI model call (Groq SSE)
  │
  ▼
SSE token stream → frontend → terminal render
```

### File Structure

```
EIGENFORM/
├── run.py                          Entry point
├── backend/
│   ├── main.py                     Flask app factory
│   ├── config.py                   Settings loader
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py             POST /api/chat (main endpoint)
│   │       ├── session.py          GET/DELETE /api/session
│   │       ├── status.py           GET /api/status
│   │       └── interrupt.py        POST /api/interrupt
│   ├── ai/
│   │   ├── core/
│   │   │   ├── engine.py           Model API, streaming, tool call handling
│   │   │   └── dispatcher.py       Command pattern matching and routing
│   │   ├── memory/
│   │   │   └── short_term.py       In-memory session state (thread-safe)
│   │   └── personality/
│   │       ├── rocky.py            System prompt generator
│   │       └── responses.py        Hardcoded status messages
│   └── systems/
│       ├── executor.py             Command executor (open_url, search_youtube)
│       ├── apps/                   [STUB] App launcher
│       ├── files/                  [STUB] File operations
│       ├── os_control/             [STUB] OS control (volume, window focus)
│       └── web/
│           └── youtube.py          YouTube URL builder (helper)
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
│       ├── api/client.js           HTTP + SSE client, frontend command interception
│       ├── core/app.js             Boot sequence, input handling, state
│       ├── terminal/terminal.js    Token rendering, streaming lines
│       └── ui/                     HUD, themes, animations
├── data/
│   ├── config/settings.json        Runtime configuration
│   └── apps/app_registry.json      Known app paths (not yet used)
└── docs/
    └── spec.md                     This file
```

### Key Design Rules

1. **Commands never go through the AI.** Pattern matching in the dispatcher intercepts action requests before the model is called. The model cannot be relied upon to output structured commands.
2. **System prompt is injected on every request.** It is never cached between calls.
3. **Session memory is append-only.** Only full user+assistant exchanges are written. Partial or interrupted responses are discarded.
4. **The dispatcher is the authority on what is a command.** If a message matches a command pattern, the AI is not contacted.

---

## 3. Phase 1 — Completed

### What Was Built

| Component | Status | Notes |
|-----------|--------|-------|
| Flask backend + SSE streaming | ✅ Complete | Dual format: OpenAI + Ollama |
| Terminal UI (text) | ✅ Complete | Streaming render, themes, HUD |
| Rocky personality system | ✅ Complete | Voice seed, tone reminder, structured prompt |
| Session memory (in-process) | ✅ Complete | Thread-safe, 20-message window |
| Hard interrupt | ✅ Complete | Escape / STOP button / AbortController |
| YouTube command (frontend) | ✅ Complete | Opens search results in new tab |
| Spotify playlist open | ✅ Complete | Opens desktop app via URI |
| Status polling | ✅ Complete | Online/offline ring, 30s interval |
| Theme system | ✅ Complete | 6+ colour schemes |
| Config system | ✅ Complete | settings.json, frozen + source mode |

### Known Issues Carried Forward

- **Duplicate command logic** exists in three places: `client.js`, `chat.py`, and `dispatcher.py`. These need to be consolidated into the dispatcher in Phase 2.
- **API key is stored in plaintext** in `settings.json`. Needs to move to an environment variable or encrypted store.
- **Voice input/output** is completely stubbed — `speech.js` and `synthesis.js` are no-ops.
- **README.md has a merge conflict** from a previous repo and is not valid documentation.
- **`commands_bp` blueprint** is defined but never registered in `main.py`.
- **Long-term memory** (`long_term.py`, `context.py`) is not implemented — memory resets on server restart.

---

## 4. Phase 2 — In Progress

### Goals

Turn EIGENFORM from a working chatbot UI into a reliable, extensible AI assistant that can take real actions on the user's computer — deterministically, safely, and with clear user feedback.

### A. Command System Overhaul

**Problem:** Command detection is duplicated across three files and is not extensible. Adding a new command requires editing multiple files.

**Solution:** Consolidate all command matching into the dispatcher. The dispatcher becomes the single authority. Frontend and `chat.py` remove their own pattern matching and defer entirely to dispatcher output.

**Implementation:**

1. Create `backend/systems/registry.py` — a central command registry:
   ```python
   # Each command entry:
   {
       "name": "search_youtube",
       "patterns": [r"\bplay\b.{0,60}\byoutube\b"],
       "extract": fn(message) -> dict,
       "handler": fn(args) -> str,
       "description": "Search YouTube for a song or video",
   }
   ```

2. Each system module (`apps/`, `web/`, `files/`, `os_control/`) defines a `register()` function that returns its command entries. The registry auto-discovers and loads them at startup.

3. `dispatcher.py` queries the registry on every request. If a pattern matches with sufficient confidence, it runs the handler directly. Otherwise it calls the AI engine.

4. Remove `_try_command()` from `chat.py` and `_tryCommand()` from `client.js`. The dispatcher handles everything. The frontend only needs to render the SSE response.

5. Add a new SSE event type `{"type": "command_executed", "name": "...", "args": {...}}` so the frontend can show visual feedback when a command runs.

**Success criteria:**
- Adding a new command requires creating one file and one `register()` function. No other files change.
- The same command works whether triggered by text or voice.
- Zero duplicate pattern matching across the codebase.

---

### B. App Launcher

**Problem:** `backend/systems/apps/launcher.py` and `registry.py` are empty. Rocky cannot open desktop applications.

**Implementation:**

1. `backend/systems/apps/registry.py` — loads `data/apps/app_registry.json`:
   ```json
   {
     "chrome":   { "path": "C:\\...\\chrome.exe",   "aliases": ["chrome", "browser", "google chrome"] },
     "notepad":  { "path": "notepad.exe",            "aliases": ["notepad", "text editor"] },
     "vscode":   { "path": "C:\\...\\Code.exe",      "aliases": ["vscode", "vs code", "code editor"] },
     "spotify":  { "path": "C:\\...\\Spotify.exe",   "aliases": ["spotify", "music app"] },
     "explorer": { "path": "explorer.exe",            "aliases": ["explorer", "file explorer", "files"] }
   }
   ```

2. `backend/systems/apps/launcher.py` — executes the launch:
   ```python
   def launch_app(name: str) -> str:
       # Look up in registry, validate path exists, subprocess.Popen
       # Returns confirmation or error message
   ```

3. Register as a command: `"open {app}"`, `"launch {app}"`, `"start {app}"`

4. Entity extraction: strip "open"/"launch"/"start" from the message, fuzzy-match remainder against all known aliases using difflib.

**Safety:** Only paths listed in `app_registry.json` can be launched. No arbitrary executable paths accepted.

**Success criteria:**
- "open chrome", "launch notepad", "open file explorer" all work.
- Unknown app names return a clear error: "I don't have {name} registered."

---

### C. Web Search

**Problem:** Rocky can open YouTube but cannot search the web generally.

**Implementation:**

1. Command patterns: `"search for X"`, `"look up X"`, `"google X"`, `"find X online"`

2. Handler opens: `https://www.google.com/search?q={query}` in the default browser.

3. Optional: DuckDuckGo as an alternative (`https://duckduckgo.com/?q={query}`).

**Success criteria:**
- "search for the weather in New York" opens a Google search results page.

---

### D. Visual Command Feedback

**Problem:** When a command executes, the user sees Rocky's text confirmation but no visual indication that something happened on the OS level.

**Implementation:**

1. New SSE event: `{"type": "command_executed", "name": "search_youtube", "args": {"query": "Bohemian Rhapsody"}}`

2. Frontend renders a distinct line type for executed commands — different prefix and colour from normal chat. Example:
   ```
   ⚡ search_youtube → "Bohemian Rhapsody"
   ```

3. Command lines are not saved to session history (they are ephemeral UI feedback).

**Success criteria:**
- Every executed command produces a visible indicator in the terminal distinct from Rocky's chat response.

---

### E. Logging and Debug Visibility

**Problem:** When something breaks, there is no structured log output. `print()` statements were added ad-hoc for debugging.

**Implementation:**

1. Replace ad-hoc `print()` calls with Python's `logging` module.

2. Log levels:
   - `DEBUG`: full request payload, pattern match results, raw model response
   - `INFO`: command executed, session created, model call started/completed
   - `WARNING`: pattern matched but handler failed, retry triggered
   - `ERROR`: model unreachable, handler exception

3. Log format: `[timestamp] [LEVEL] [module] message`

4. Configurable log level via `settings.json`: `"log_level": "INFO"`

5. Optional: write to `logs/eigenform.log` alongside console output.

**Success criteria:**
- Every request produces at least one `INFO` log line.
- When a command executes, the log shows which pattern matched and which handler ran.
- When the model is called, the log shows the message count sent.

---

### F. Memory Persistence

**Problem:** Session memory resets every time the server restarts. Rocky forgets everything.

**Implementation:**

1. On session update, write the message list to `data/sessions/{session_id}.json`.

2. On server start, if a session file exists, load it into memory before the first request.

3. Cap stored sessions at 7 days. Delete older files on startup.

4. `long_term.py` — extract key facts from conversations (name, preferences, recurring tasks) and store in `data/memory/facts.json`. Inject relevant facts into the system prompt on each request.

**Success criteria:**
- Rocky remembers the last conversation after a server restart.
- Rocky knows the user's name if they've told him before.

---

### Phase 2 Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| App paths vary between machines | High | Validate path exists at launch, surface clear error |
| Regex patterns produce false positives | Medium | Test all patterns against a fixed input set before shipping |
| Duplicate command logic causes split behaviour | High | Remove frontend/chat.py patterns before shipping dispatcher registry |
| Session file corruption on crash | Low | Write to temp file, rename on success (atomic write) |
| Log volume too high in INFO mode | Medium | Default to WARNING in production; INFO only in dev |

### Phase 2 Success Criteria

- [ ] All commands route through the dispatcher registry. No duplicate pattern matching.
- [ ] "open chrome", "open notepad", "open spotify" all launch the correct app.
- [ ] "search for X" opens a browser search.
- [ ] Executed commands produce a visual indicator in the terminal.
- [ ] Structured logging replaces all ad-hoc `print()` calls.
- [ ] Session memory persists across server restarts.
- [ ] Adding a new command requires creating one file only.

---

## 5. Phase 3 — Future

### Voice Input / Output

- **STT:** Web Speech API (`speech.js`) — already stubbed. Activate with wake word "hey rocky" or push-to-talk.
- **TTS:** Web Speech API (`synthesis.js`) — already stubbed. Voice settings (rate, pitch, language) are already in `settings.json`.
- **Interruption:** Wake word detection mid-speech cancels current TTS and starts a new request.
- **Audio visualizer:** Waveform animation during voice input/output (`visualizer.js` stub).

### File System Operations

- Read files within `allowed_dirs` (configured in `settings.json`).
- Search files by name or content within allowed scope.
- Summarise file contents on request.
- Write files only with explicit user confirmation.

### OS Control

- Volume up/down/mute (via `pycaw` or `ctypes`).
- Brightness control (via `screen_brightness_control`).
- Window focus management (via `pygetwindow`).
- Process list and kill (via `psutil`).

### Extended AI Capabilities

- Long-term memory with fact extraction and relevance injection.
- Multi-turn task planning: Rocky breaks a goal into steps and executes them sequentially.
- Web scraping for real-time data (weather, news headlines).

### Packaging

- PyInstaller single-executable build.
- Auto-update mechanism.
- Windows startup integration (optional, opt-in).

---

## 6. Settings Schema

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_format` | string | `"openai"` | `"openai"` or `"ollama"` |
| `model_api_url` | string | Groq endpoint | Full API URL |
| `model_name` | string | `"llama-3.3-70b-versatile"` | Model identifier |
| `api_key` | string | — | **Move to env var: `EIGENFORM_API_KEY`** |
| `model_temperature` | float | `0.4` | Sampling temperature |
| `model_timeout_seconds` | int | `60` | Read timeout |
| `model_retry_count` | int | `1` | Retries on connection failure |
| `ai_name` | string | `"Rocky"` | AI display name |
| `user_name` | string | `""` | User's name (injected into prompt) |
| `voice_enabled` | bool | `true` | Enable TTS/STT (Phase 3) |
| `voice_lang` | string | `"en-GB"` | BCP-47 language code |
| `voice_rate` | float | `0.90` | TTS speech rate |
| `voice_pitch` | float | `0.85` | TTS pitch |
| `wake_word` | string | `"hey rocky"` | STT activation phrase |
| `always_listen` | bool | `false` | Continuous listening mode |
| `max_short_term_messages` | int | `20` | Rolling context window size |
| `allowed_dirs` | array | `["Documents", "Desktop"]` | File operation scope |
| `log_level` | string | `"WARNING"` | Logging verbosity |
| `flask_host` | string | `"127.0.0.1"` | Bind address |
| `flask_port` | int | `5000` | Bind port |
| `flask_debug` | bool | `false` | Flask debug mode |

---

## 7. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Main chat endpoint — SSE streaming response |
| `GET` | `/api/status` | Model health check |
| `GET` | `/api/session` | Retrieve session message history |
| `DELETE` | `/api/session` | Clear session memory |
| `POST` | `/api/interrupt` | Cancel active stream |
| `GET` | `/auth/spotify/callback` | Spotify OAuth callback (if implemented) |

### SSE Event Types (POST /api/chat)

| Type | Payload | Description |
|------|---------|-------------|
| `token` | `{ content: string }` | Streamed text fragment |
| `done` | — | Stream complete |
| `error` | `{ code, message }` | Model or server error |
| `interrupted` | — | Stream cancelled by user |
| `command_executed` | `{ name, args }` | Command ran (Phase 2) |

---

## 8. Security Model

### Enforced Constraints

- **No arbitrary code execution.** The dispatcher only runs handlers registered in the command registry. Unrecognised patterns go to the AI for a text response only.
- **No arbitrary app launch.** Only executables listed in `app_registry.json` can be launched.
- **No arbitrary file access.** File operations are scoped to paths within `allowed_dirs`.
- **No shell commands.** `subprocess.Popen` is called with explicit argument lists only — never `shell=True`.
- **Local only.** Flask binds to `127.0.0.1`. No external exposure.

### Known Vulnerabilities (To Fix in Phase 2)

1. **API key in plaintext.** `settings.json` stores the Groq API key in plain text. Move to environment variable `EIGENFORM_API_KEY` and read with `os.environ.get()`.
2. **No URL validation on open_url.** The `open_url` handler accepts any URL. Add a scheme whitelist (`https://` only) and optionally a domain allowlist.
3. **No rate limiting.** Rapid repeated requests could exhaust Groq API quota. Add a simple per-session request throttle.
