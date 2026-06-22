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

## Deploy to Cloudflare Pages (free, always-on, no server to manage)

This is the recommended way to run Jarvis for real. No VM, no sysadmin work,
no sleep/cold-start delay — Cloudflare's free tier runs the backend as
on-demand serverless functions (100k requests/day) and serves the frontend
as static files, both from the same domain.

The `functions/` directory is a parallel implementation of the same backend
in `server/` (auth, chat, tool registry), written for Cloudflare's Workers
runtime instead of Flask, using Cloudflare KV instead of local JSON files for
storage (serverless functions have no persistent filesystem).

1. Push this repo to GitHub (already done).
2. In the [Cloudflare dashboard](https://dash.cloudflare.com), go to
   **Workers & Pages → Create → Pages → Connect to Git**, pick this repo.
   Build settings: no build command needed, output directory `client`.
3. **Create a KV namespace**: Workers & Pages → KV → Create namespace (e.g.
   `jarvis`). Then on your Pages project: Settings → Functions → KV namespace
   bindings → add binding, variable name `JARVIS_KV`, pointing at that
   namespace.
4. **Add environment variables/secrets**: Settings → Environment variables,
   add (as *secrets*, not plain text): `SECRET_KEY` (any random string),
   `JOEL_PASSWORD`, `VALERIE_PASSWORD`, `AI_PROVIDER` (`groq` by default),
   `GROQ_API_KEY` (or the equivalent for whichever provider you choose).
5. Redeploy (Cloudflare auto-deploys on every push to `main` once connected).
6. Open the `*.pages.dev` URL Cloudflare gives you — HTTPS is automatic. You
   can later attach a custom domain for free under the same project.

This keeps the original security model intact: the LLM API key lives only in
Cloudflare's environment, never in the browser.

## Deploy to a free always-on VM (Google Cloud)

This makes Jarvis reachable from your phone over the internet, regardless of
whether any of your own computers are on.

1. Create a free `e2-micro` VM on Google Cloud — must be in `us-west1`,
   `us-central1`, or `us-east1` to qualify for the Always Free tier. Use
   Ubuntu as the image.
2. Get a free hostname pointing at the VM's external IP (e.g.
   [duckdns.org](https://www.duckdns.org)) — Caddy needs a real domain to
   issue a free HTTPS certificate, a bare IP won't work.
3. SSH into the VM and run:
   ```bash
   git clone https://github.com/Joel-Trumpet-67/Jarvis.git
   sudo JARVIS_DOMAIN=yourname.duckdns.org bash Jarvis/deploy/setup-vm.sh
   ```
4. Edit secrets on the VM: `sudo nano /opt/jarvis/.env`, then
   `sudo systemctl restart jarvis`.
5. Open `https://yourname.duckdns.org` from your phone, from anywhere.

This runs Jarvis under `gunicorn` (not the Flask dev server) as a systemd
service that restarts on crash/reboot, bound to localhost only — Caddy is the
only process exposed to the internet, terminating HTTPS and proxying to
Jarvis. `DEBUG` is forced off in this setup (the Flask debugger allows
arbitrary code execution and must never be enabled on a public-facing
server).

## Accounts

- **Joel** — owner. Full chat/voice, tool registry visible, can approve/reject pending tools.
- **Valerie** — guest. Full chat/voice, tool registry is read-only, no approve/reject.

Each account has its own conversation history and profile (`data/users/<name>/`), so what Jarvis learns about one stays off the other's.

## How Jarvis learns and extends itself

- Tell it something explicitly ("remember that I prefer X") or correct it ("that's wrong, it's actually X") — it updates `data/users/<name>/profile.json` and won't repeat a corrected mistake.
- If a request needs a capability that doesn't exist, Jarvis writes the tool itself and drops it into `data/tools/registry.json` with `approved: false`. It shows up on Joel's pending-tools card (bottom of the UI) with a plain-English description and expandable code. Approve or reject from there; rejections are remembered so it won't propose the same tool twice.

## Project structure

```
server/             Flask backend — used for local dev and the VM deploy path
  app.py            Flask app factory, route registration
  config.py         env-based config, user accounts
  routes/           auth, chat, tools — one file per feature area
  services/
    llm.py          provider-agnostic chat() — Groq/OpenAI/Ollama/Anthropic
    ai.py           system prompt, tool-proposal + memory-update parsing
    memory.py       per-user profile + history persistence
    registry.py     tool registry persistence
functions/          Cloudflare Pages Functions backend — same behavior as
                    server/, ported to serverless + KV for the Pages deploy
  _lib/             auth (signed cookies), users, kv, llm, ai — JS ports of
                    the equivalent server/ modules
  api/              one file/folder per route, mirrors server/routes/
client/
  index.html, app.js, api.js, voice.js, styles.css
  manifest.json, service-worker.js   PWA install + offline shell caching
data/
  users/joel/, users/valerie/        profile.json, history.json (local/VM only)
  tools/registry.json                                  (local/VM only)
deploy/             setup script + systemd/Caddy config for the VM deploy path
```

## What's not built yet

PC agent / Tailscale control, iOS Shortcuts bridge, self-editing source with git rollback, daily briefing, weather/calendar, push notifications, GPS/camera/clipboard. These don't exist as stubs — they're just not started.
