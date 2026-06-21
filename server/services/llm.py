from anthropic import Anthropic
from openai import OpenAI

from server.config import (
    AI_MODEL,
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    GROQ_API_KEY,
    OLLAMA_BASE_URL,
    OPENAI_API_KEY,
)


def _anthropic_chat(system_prompt, messages, max_tokens):
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _openai_compatible_client():
    if AI_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured")
        return OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

    if AI_PROVIDER == "ollama":
        return OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL)

    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return OpenAI(api_key=OPENAI_API_KEY)

    raise RuntimeError(f"Unknown AI_PROVIDER '{AI_PROVIDER}'")


def _openai_compatible_chat(system_prompt, messages, max_tokens):
    client = _openai_compatible_client()
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
    except Exception as exc:
        raise RuntimeError(f"{AI_PROVIDER} request failed: {exc}") from exc
    return response.choices[0].message.content or ""


def chat(system_prompt, messages, max_tokens=1024):
    if AI_PROVIDER == "anthropic":
        return _anthropic_chat(system_prompt, messages, max_tokens)
    return _openai_compatible_chat(system_prompt, messages, max_tokens)
