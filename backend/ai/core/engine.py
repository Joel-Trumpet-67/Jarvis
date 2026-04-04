"""
engine.py — Calls the Ollama AI model API with streaming enabled.

Yields SSE-compatible event dicts that chat.py wraps and sends to the frontend.
Checks session cancel_requested on every token — stops mid-stream if interrupted.

Ollama streaming format:
  POST http://localhost:11434/api/chat
  Body: {"model": "mistral", "messages": [...], "stream": true}
  Response: newline-delimited JSON
    {"message": {"role": "assistant", "content": "token"}, "done": false}
    {"message": {"role": "assistant", "content": ""}, "done": true, ...}
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import json
import time
import requests
from typing import Generator

from backend.config import CONFIG
from backend.ai.memory.short_term import get_session


def _build_messages(session_id: str, user_message: str, system_prompt: str) -> list:
    """
    Assemble the messages array for the Ollama API.
    Format: [system, ...history, user_message]
    """
    max_msgs = CONFIG.get("max_short_term_messages", 20)
    session = get_session(session_id)
    history = session.get_messages(max_count=max_msgs)

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        messages.append({
            "role":    msg["role"],
            "content": msg["content"],
        })

    messages.append({"role": "user", "content": user_message})
    return messages


def stream_response(
    session_id: str,
    user_message: str,
    system_prompt: str,
) -> Generator[dict, None, None]:
    """
    Generator that streams tokens from the Ollama API.

    Yields dicts (these become SSE events in chat.py):
      {"type": "token",       "content": "..."}
      {"type": "done"}
      {"type": "interrupted"}
      {"type": "error",       "code": "...", "message": "..."}
    """
    session = get_session(session_id)
    session.clear_cancel()

    messages = _build_messages(session_id, user_message, system_prompt)

    payload = {
        "model":      CONFIG.get("model_name", "mistral"),
        "messages":   messages,
        "stream":     True,
        "keep_alive": "10m",   # Keep model loaded in memory for 10 mins between requests
    }

    api_url    = CONFIG.get("model_api_url", "http://localhost:11434/api/chat")
    max_retry  = CONFIG.get("model_retry_count", 1)

    # Tuple timeout: (connect_seconds, read_seconds)
    # Connect should be fast. Read can be very long — model may need time
    # to load into memory on first inference (especially mistral on cold start).
    connect_timeout = 10
    read_timeout    = CONFIG.get("model_timeout_seconds", 120)
    timeout = (connect_timeout, read_timeout)

    for attempt in range(max_retry + 1):
        try:
            response = requests.post(
                api_url,
                json=payload,
                stream=True,
                timeout=timeout,
            )
            response.raise_for_status()

            collected_tokens = []

            for raw_line in response.iter_lines():
                # Hard interrupt check — every single token
                if session.is_cancelled():
                    yield {"type": "interrupted"}
                    return

                if not raw_line:
                    continue

                try:
                    chunk = json.loads(raw_line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

                if chunk.get("done"):
                    break

                token = chunk.get("message", {}).get("content", "")
                if token:
                    collected_tokens.append(token)
                    yield {"type": "token", "content": token}

            # Write complete exchange to session memory only after full response
            if collected_tokens:
                full_text = "".join(collected_tokens)
                session.add_message("user", user_message)
                session.add_message("assistant", full_text)

            yield {"type": "done"}
            return

        except requests.exceptions.ConnectionError:
            if attempt < max_retry:
                time.sleep(2)
                continue
            yield {
                "type":    "error",
                "code":    "MODEL_OFFLINE",
                "message": (
                    "My neural link appears to be offline, sir. "
                    "Attempting reconnection."
                ),
            }
            return

        except requests.exceptions.Timeout:
            if attempt < max_retry:
                time.sleep(2)
                continue
            yield {
                "type":    "error",
                "code":    "MODEL_TIMEOUT",
                "message": (
                    "The AI core is taking longer than expected, sir. "
                    "Please try again."
                ),
            }
            return

        except requests.exceptions.HTTPError as e:
            yield {
                "type":    "error",
                "code":    "HTTP_ERROR",
                "message": (
                    f"The model returned an unexpected response, sir. "
                    f"Status: {e.response.status_code}"
                ),
            }
            return

        except Exception as e:
            yield {
                "type":    "error",
                "code":    "UNKNOWN",
                "message": f"Something went wrong on my end, sir. ({type(e).__name__})",
            }
            return
