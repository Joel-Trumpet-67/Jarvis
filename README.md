# Jarvis

A personal AI assistant for Joel, with a separate guest account for Valerie. Flask backend, vanilla JS PWA frontend, pluggable LLM backend (Groq by default).

## Setup

```bash
git clone <your repo URL>
cd Jarvis
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

| Variable | Required for | Notes |
|---|---|---|
| `SECRET_KEY` | always | any random string |
| `JOEL_PASSWORD` | always | Joel's login password |
| `VALERIE_PASSWORD` | always | Valerie's login password |
| `AI_PROVIDER` | always | `groq` (default), `anthropic`, `openai`, or `ollama` |
| `GROQ_API_KEY` | `AI_PROVIDER=groq` | console.groq.com |
| `ANTHROPIC_API_KEY` | `AI_PROVIDER=anthropic` | console.anthropic.com |
| `OPENAI_API_KEY` | `AI_PROVIDER=openai` | platform.openai.com |
| `OLLAMA_BASE_URL` | `AI_PROVIDER=ollama` | defaults to `http://localhost:11434/v1`, needs `ollama pull <model>` first |

`AI_MODEL` is optional — each provider has a sensible default, override only if you want a specific model.

## Run

```bash
python run.py
```

Open `http://localhost:5000` and log in as `joel` or `valerie`.

## Install on iPhone

Phone needs to reach the machine running the server (same WiFi, or eventually via Tailscale). In Safari, open `http://<your-computer's-LAN-IP>:5000`, then Share → Add to Home Screen.

## Accounts

- **Joel** — owner. Full chat/voice, tool registry visible, can approve/reject pending tools.
- **Valerie** — guest. Full chat/voice, tool registry is read-only, no approve/reject.

Each account has its own conversation history and profile (`data/users/<name>/`), so what Jarvis learns about one stays off the other's.

## How Jarvis learns and extends itself

- Tell it something explicitly ("remember that I prefer X") or correct it ("that's wrong, it's actually X") — it updates `data/users/<name>/profile.json` and won't repeat a corrected mistake.
- If a request needs a capability that doesn't exist, Jarvis writes the tool itself and drops it into `data/tools/registry.json` with `approved: false`. It shows up on Joel's pending-tools card (bottom of the UI) with a plain-English description and expandable code. Approve or reject from there; rejections are remembered so it won't propose the same tool twice.

## Project structure

```
server/
  app.py            Flask app factory, route registration
  config.py         env-based config, user accounts
  routes/           auth, chat, tools — one file per feature area
  services/
    llm.py          provider-agnostic chat() — Groq/OpenAI/Ollama/Anthropic
    ai.py           system prompt, tool-proposal + memory-update parsing
    memory.py       per-user profile + history persistence
    registry.py     tool registry persistence
client/
  index.html, app.js, api.js, voice.js, styles.css
  manifest.json, service-worker.js   PWA install + offline shell caching
data/
  users/joel/, users/valerie/        profile.json, history.json
  tools/registry.json
```

## What's not built yet

PC agent / Tailscale control, iOS Shortcuts bridge, self-editing source with git rollback, daily briefing, weather/calendar, push notifications, GPS/camera/clipboard. These don't exist as stubs — they're just not started.
