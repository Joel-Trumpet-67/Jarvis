"""
engine.py — Calls the AI model API with streaming enabled.

Supports two API formats controlled by 'api_format' in settings.json:

  "ollama"  — Ollama local API (http://localhost:11434/api/chat)
              Streaming: newline-delimited JSON
              Token path: chunk["message"]["content"]

  "openai"  — OpenAI-compatible API (Groq, OpenAI, LM Studio, etc.)
              Streaming: SSE lines starting with 'data: '
              Token path: chunk["choices"][0]["delta"]["content"]
              Requires: api_key in settings.json

Yields SSE-compatible event dicts that chat.py wraps and sends to the frontend.
Checks session cancel_requested on every token — stops mid-stream if interrupted.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import re
import json
import time
import requests
from typing import Generator

from backend.config import CONFIG
from backend.ai.memory.short_term import get_session


def _sanitize(text: str, ai_name: str) -> str:
    """
    Replace any Jarvis identity slips with the correct AI name.
    Operates on complete strings (not per-token) to catch split patterns.
    """
    text = re.sub(r'J\.A\.R\.V\.I\.S\.?', ai_name, text, flags=re.IGNORECASE)
    text = re.sub(r'\bJARVIS\b', ai_name, text, flags=re.IGNORECASE)
    return text


_TONE_REMINDER = (
    "Reminder: you are Rocky. Calm, dry, efficient. You execute tasks — you do not guide. "
    "No emojis. No filler openers. No sycophancy. No emotional support language. No slang. "
    "Speak like a capable person, not a chatbot. Do not label responses. Do not end with 'Proceed.'"
)

_REMINDER_EVERY_N = 6  # Inject a tone reminder every N messages


_VOICE_SEED = [
    {"role": "user",      "content": "Who are you?"},
    {"role": "assistant", "content": "I'm Rocky. I run EIGENFORM — system control, task execution, questions. What do you need?"},
    {"role": "user",      "content": "What can you do?"},
    {"role": "assistant", "content": "Handle your system, open apps, search the web, manage files, answer questions. Tell me what needs doing."},
    {"role": "user",      "content": "Play Bohemian Rhapsody on YouTube"},
    {"role": "assistant", "content": '{"action": "search_youtube", "query": "Bohemian Rhapsody Queen"}'},
    {"role": "user",      "content": "Open Google"},
    {"role": "assistant", "content": '{"action": "open_url", "url": "https://www.google.com"}'},
]


def _build_messages(session_id: str, user_message: str, system_prompt: str) -> list:
    """
    Assemble the messages array for the model API.
    Format: [system, voice_seed, ...history, (tone reminder if due), user_message]

    Voice seed: two pre-baked exchanges that anchor Rocky's tone before the
    real conversation starts. This prevents the model from freestyling on the
    opening message, which is when personality drift is worst.

    Tone reminder: injected every REMINDER_EVERY_N messages to fight drift
    in longer conversations.
    """
    max_msgs = CONFIG.get("max_short_term_messages", 20)
    session  = get_session(session_id)
    history  = session.get_messages(max_count=max_msgs)

    messages = [{"role": "system", "content": system_prompt}]

    # Always prepend voice seed to anchor tone from message one
    messages.extend(_VOICE_SEED)

    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Re-inject tone reminder periodically to fight model drift
    if len(history) > 0 and (len(history) % _REMINDER_EVERY_N) < 2:
        messages.append({"role": "system", "content": _TONE_REMINDER})

    messages.append({"role": "user", "content": user_message})
    return messages


def _extract_token_ollama(raw_line: bytes) -> str | None:
    """Parse one streaming line from Ollama format."""
    try:
        chunk = json.loads(raw_line.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if chunk.get("done"):
        return None
    return chunk.get("message", {}).get("content") or None


def _extract_token_openai(raw_line: bytes) -> str | None:
    """Parse one streaming line from OpenAI/Groq SSE format."""
    try:
        line = raw_line.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None

    if not line.startswith("data: "):
        return None
    data = line[6:]
    if data == "[DONE]":
        return None
    try:
        chunk = json.loads(data)
    except json.JSONDecodeError:
        return None

    delta = chunk.get("choices", [{}])[0].get("delta", {})
    return delta.get("content") or None


def stream_response(
    session_id: str,
    user_message: str,
    system_prompt: str,
) -> Generator[dict, None, None]:
    """
    Generator that streams tokens from the AI model API.

    Yields dicts (these become SSE events in chat.py):
      {"type": "token",       "content": "..."}
      {"type": "done"}
      {"type": "interrupted"}
      {"type": "error",       "code": "...", "message": "..."}
    """
    session  = get_session(session_id)
    session.clear_cancel()
    ai_name  = CONFIG.get("ai_name", "Rocky")

    messages   = _build_messages(session_id, user_message, system_prompt)
    api_format = CONFIG.get("api_format", "ollama")
    api_url    = CONFIG.get("model_api_url", "http://localhost:11434/api/chat")
    api_key    = CONFIG.get("api_key", "")
    model_name = CONFIG.get("model_name", "mistral")
    max_retry  = CONFIG.get("model_retry_count", 1)
    timeout    = (10, CONFIG.get("model_timeout_seconds", 60))

    temperature = CONFIG.get("model_temperature", 0.4)

    # Build payload and headers based on format
    if api_format == "openai":
        from backend.systems.executor import TOOL_DEFINITIONS
        payload = {
            "model":       model_name,
            "messages":    messages,
            "stream":      True,
            "temperature": temperature,
            "tools":       TOOL_DEFINITIONS,
            "tool_choice": "auto",
        }
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        }
    else:
        # Ollama format
        payload = {
            "model":      model_name,
            "messages":   messages,
            "stream":     True,
            "keep_alive": "10m",
            "options":    {"temperature": temperature},
        }
        headers = {"Content-Type": "application/json"}

    for attempt in range(max_retry + 1):
        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                stream=True,
                timeout=timeout,
            )
            response.raise_for_status()

            collected_tokens = []
            token_buffer = ""   # Rolling buffer for sanitization
            thinking = False    # True while inside <think>...</think> block
            tool_calls_acc = {} # index -> {name, arguments} for native tool calling

            for raw_line in response.iter_lines():
                # Hard interrupt check on every token
                if session.is_cancelled():
                    yield {"type": "interrupted"}
                    return

                if not raw_line:
                    continue

                # ── OpenAI/Groq streaming ──────────────────────────────────
                if api_format == "openai":
                    try:
                        line = raw_line.decode("utf-8").strip()
                    except UnicodeDecodeError:
                        continue
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    choice = chunk.get("choices", [{}])[0]
                    delta  = choice.get("delta", {})

                    # Accumulate tool call fragments
                    for tc in delta.get("tool_calls", []):
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {"name": "", "arguments": ""}
                        func = tc.get("function", {})
                        tool_calls_acc[idx]["name"]      += func.get("name", "")
                        tool_calls_acc[idx]["arguments"] += func.get("arguments", "")

                    token = delta.get("content") or ""

                # ── Ollama streaming ───────────────────────────────────────
                else:
                    token = _extract_token_ollama(raw_line) or ""

                if not token:
                    continue

                # Suppress <think>...</think> reasoning blocks (Qwen3 etc.)
                token_buffer += token
                if "<think>" in token_buffer:
                    thinking = True
                if thinking:
                    if "</think>" in token_buffer:
                        token_buffer = token_buffer.split("</think>", 1)[1]
                        thinking = False
                    else:
                        continue

                clean = _sanitize(token_buffer, ai_name)

                # Emit safe portion, keep last 20 chars buffered to catch split patterns
                if len(clean) > 20:
                    emit = clean[:-20]
                    token_buffer = clean[-20:]
                    collected_tokens.append(emit)
                    yield {"type": "token", "content": emit}

            # Flush remaining buffer
            if token_buffer and not thinking:
                final = _sanitize(token_buffer, ai_name)
                collected_tokens.append(final)
                yield {"type": "token", "content": final}

            # ── Native tool call detected ──────────────────────────────────
            if tool_calls_acc:
                for idx, tc in sorted(tool_calls_acc.items()):
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    yield {"type": "tool_call", "name": tc["name"], "args": args}
                # Save the intent to memory so context isn't lost
                session.add_message("user", user_message)
                session.add_message("assistant", f"[tool: {list(tool_calls_acc.values())[0]['name']}]")
                yield {"type": "done"}
                return

            # Write complete exchange to session memory after full response
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
                "message": "Can't reach the AI core. Check your connection.",
            }
            return

        except requests.exceptions.Timeout:
            if attempt < max_retry:
                time.sleep(2)
                continue
            yield {
                "type":    "error",
                "code":    "MODEL_TIMEOUT",
                "message": "Response timed out. Try again.",
            }
            return

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            msg = "Invalid API key — check your settings." if status == 401 else \
                  f"Unexpected response from the model. (HTTP {status})"
            yield {"type": "error", "code": "HTTP_ERROR", "message": msg}
            return

        except Exception as e:
            yield {
                "type":    "error",
                "code":    "UNKNOWN",
                "message": f"Something went wrong. ({type(e).__name__})",
            }
            return
