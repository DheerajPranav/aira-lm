"""Aira chat — the engine that connects memory to a generation backend.

Runs the full pipeline (guard → decide → mutate → retrieve → compose → generate) against
a deterministic ``MockBackend``, degrading to a no-memory response on any memory failure.
No PyTorch, web UI or network here; Aira Core integration arrives in Step 13.
"""

from __future__ import annotations

from aira.chat.backend import GenerationBackend, GenerationRequest, MockBackend
from aira.chat.engine import ChatEngine, create_chat_engine
from aira.chat.models import ChatDebug, ChatResponse, SessionStats
from aira.chat.session import run_session

__all__ = [
    "ChatDebug",
    "ChatEngine",
    "ChatResponse",
    "GenerationBackend",
    "GenerationRequest",
    "MockBackend",
    "SessionStats",
    "create_chat_engine",
    "run_session",
]
