"""Response and session-stats types for chat."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChatDebug:
    """Debug-only metadata. Present only when a request enables debug mode."""

    capture_reasons: tuple[str, ...]
    retrieval_count: int
    included_memory_ids: tuple[str, ...]
    context_token_count: int
    memory_block: str


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """The result of one chat turn.

    ``correlation_id`` and ``latency_ms`` are always present (observability, not debug).
    ``debug`` is populated only when the caller enabled debug mode; user-visible ``text``
    never exposes internal ids otherwise.
    """

    text: str
    correlation_id: str
    latency_ms: float
    memory_used: bool
    degraded: bool
    debug: ChatDebug | None = None


@dataclass(slots=True)
class SessionStats:
    """Mutable per-session counters for the ``/stats`` command."""

    messages: int = 0
    memory_used: int = 0
    degraded: int = 0
    total_latency_ms: float = 0.0

    def record(self, response: ChatResponse) -> None:
        """Fold one response into the running counters."""
        self.messages += 1
        self.memory_used += int(response.memory_used)
        self.degraded += int(response.degraded)
        self.total_latency_ms += response.latency_ms

    @property
    def average_latency_ms(self) -> float:
        """Mean latency across recorded turns (0 when none)."""
        return round(self.total_latency_ms / self.messages, 3) if self.messages else 0.0
