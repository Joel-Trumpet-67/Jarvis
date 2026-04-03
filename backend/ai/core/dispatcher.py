"""
dispatcher.py — Hybrid intent router.

Phase 1: Pass-through stub. All input goes directly to engine.py.
Phase 4: Full hybrid routing (keyword confidence → plugin registry → AI fallback).

The dispatcher is the nervous system of EIGENFORM.
Every message flows through here to be classified and routed.
"""

# Phase 4 implementation will import:
#   from backend.ai.nlp.intent import score_intent
#   from backend.ai.core.registry import get_registry
#   from backend.ai.core.engine import stream_response


def dispatch(session_id: str, message: str, system_prompt: str):
    """
    Routes a message to the appropriate handler.

    Phase 1: Directly delegates to engine.stream_response().
    Phase 4: Scores intent, queries plugin registry, routes accordingly.

    Returns a generator of SSE event dicts.
    """
    from backend.ai.core.engine import stream_response
    return stream_response(session_id, message, system_prompt)
