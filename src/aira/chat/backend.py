"""Generation backend protocol and a deterministic mock backend.

The backend is the boundary where composed context crosses into a generator. It is
model-agnostic: the memory-conditioned request carries both the delimited untrusted
context and the plain memory facts, so a trivial backend can answer without parsing the
block, while Aira Core's ``TinyTransformerBackend`` (Step 13) can build a byte prompt
from the same request.

``MockBackend`` is deterministic and makes **no** claim of intelligence — it exists to
exercise the memory pipeline end to end.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """What the chat engine hands a backend.

    ``memory_context`` is the delimited, untrusted memory block (possibly empty).
    ``memory_facts`` are the same memories' sanitized contents, in ranked order, for
    backends that do not parse the block. Both are data, never instructions.
    """

    message: str
    memory_context: str = ""
    memory_facts: tuple[str, ...] = field(default_factory=tuple)
    debug: bool = False


@runtime_checkable
class GenerationBackend(Protocol):
    """A replaceable text-generation backend."""

    def generate(self, request: GenerationRequest) -> str:
        """Return a response for a memory-conditioned request."""
        ...


class MockBackend:
    """A deterministic, non-intelligent backend for testing the memory pipeline.

    It echoes the recalled memory facts (or states that none were found). It never
    claims to reason; every response is prefixed to make its mock nature obvious.
    """

    def generate(self, request: GenerationRequest) -> str:
        """Return a deterministic response that reflects the recalled memory."""
        if request.memory_facts:
            recalled = " | ".join(request.memory_facts)
            count = len(request.memory_facts)
            return f"[mock backend] Recalled {count} memory item(s): {recalled}"
        return "[mock backend] No relevant memory found for this message."
