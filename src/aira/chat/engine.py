"""The chat engine: the full memory-conditioned pipeline.

Order per turn: guard + decide + mutate (capture), then retrieve, rank, compose, and
generate. Memory is personalization, not a prerequisite: a failure in the write path or
the read path is isolated and the engine still returns a response with an empty memory
context (invariant 3). Retrieved memory is passed to the backend as delimited untrusted
data (invariant 8) within the configured token budget (invariant 10).
"""

from __future__ import annotations

import logging
import sqlite3
import time
import uuid
from datetime import datetime

from aira.chat.backend import GenerationBackend, GenerationRequest, MockBackend
from aira.chat.models import ChatDebug, ChatResponse
from aira.config import AiraConfig
from aira.memory.capture import CaptureService, Speaker
from aira.memory.capture.models import CaptureResult
from aira.memory.domain.clock import utc_now
from aira.memory.domain.records import MemoryRecord
from aira.memory.guard import default_guard
from aira.memory.ranking import (
    ByteTokenizer,
    DecayParams,
    Ranker,
    RankingWeights,
    Tokenizer,
    compose_memory_context,
)
from aira.memory.recall import build_retriever
from aira.memory.recall.interface import Retriever
from aira.memory.vault import MemoryRepository
from aira.memory.vault.errors import NotFoundError

_LOGGER = logging.getLogger("aira.chat")


class ChatEngine:
    """Runs one memory-conditioned turn end to end, degrading gracefully."""

    def __init__(
        self,
        *,
        capture: CaptureService,
        repository: MemoryRepository,
        retriever: Retriever,
        ranker: Ranker,
        backend: GenerationBackend,
        tokenizer: Tokenizer | None = None,
        budget: int,
        top_k: int,
        retrieve_limit: int = 50,
    ) -> None:
        """Assemble the engine from its collaborators (dependency-injected)."""
        self._capture = capture
        self._repo = repository
        self._retriever = retriever
        self._ranker = ranker
        self._backend = backend
        self._tok = tokenizer or ByteTokenizer()
        self._budget = budget
        self._top_k = top_k
        self._retrieve_limit = retrieve_limit

    def chat(
        self, owner_id: str, message: str, *, now: datetime | None = None, debug: bool = False
    ) -> ChatResponse:
        """Process one user turn and return a response, never raising on memory failure."""
        correlation_id = uuid.uuid4().hex
        stamp = now if now is not None else utc_now()
        start = time.perf_counter()

        capture_result, write_degraded = self._write_path(owner_id, message, stamp, debug)
        facts, block_text, included_ids, retrieval_count, read_degraded = self._read_path(
            owner_id, message, stamp, debug
        )

        request = GenerationRequest(
            message=message, memory_context=block_text, memory_facts=facts, debug=debug
        )
        text = self._generate(request, correlation_id)

        latency_ms = round((time.perf_counter() - start) * 1000, 3)
        degraded = write_degraded or read_degraded
        debug_meta = (
            ChatDebug(
                capture_reasons=_capture_reasons(capture_result),
                retrieval_count=retrieval_count,
                included_memory_ids=included_ids,
                context_token_count=self._tok.count(block_text) if block_text else 0,
                memory_block=block_text,
            )
            if debug
            else None
        )
        return ChatResponse(
            text=text,
            correlation_id=correlation_id,
            latency_ms=latency_ms,
            memory_used=bool(facts),
            degraded=degraded,
            debug=debug_meta,
        )

    # --- inspection helpers used by the CLI session --------------------------------

    def memories(self, owner_id: str) -> list[MemoryRecord]:
        """List an owner's active memories."""
        return self._repo.list_memories(owner_id)

    def forget(self, owner_id: str, memory_id: str, *, now: datetime | None = None) -> bool:
        """Forget a memory by id. Returns whether a memory was found and forgotten."""
        try:
            self._repo.forget(owner_id, memory_id, now=now)
        except NotFoundError:
            return False
        return True

    # --- pipeline stages -----------------------------------------------------------

    def _write_path(
        self, owner_id: str, message: str, stamp: datetime, debug: bool
    ) -> tuple[CaptureResult | None, bool]:
        try:
            result = self._capture.process(owner_id, Speaker.USER, message, now=stamp, debug=debug)
        except Exception:  # noqa: BLE001 - isolate memory-write failures from the response
            _LOGGER.warning("capture failed; continuing without a write", exc_info=False)
            return None, True
        return result, False

    def _read_path(
        self, owner_id: str, message: str, stamp: datetime, debug: bool
    ) -> tuple[tuple[str, ...], str, tuple[str, ...], int, bool]:
        try:
            results = self._retriever.search(owner_id, message, limit=self._retrieve_limit)
            ranked = self._ranker.rank(results, now=stamp)
            block = compose_memory_context(
                ranked, budget=self._budget, top_k=self._top_k, tokenizer=self._tok, debug=debug
            )
            id_to_content = {rm.memory.id: rm.memory.content for rm in ranked}
            facts = tuple(id_to_content[item.memory_id] for item in block.items)
            included_ids = tuple(item.memory_id for item in block.items)
            return facts, block.text, included_ids, len(results), False
        except Exception:  # noqa: BLE001 - degrade to no-memory generation
            _LOGGER.warning("retrieval failed; degrading to no-memory response", exc_info=False)
            return (), "", (), 0, True

    def _generate(self, request: GenerationRequest, correlation_id: str) -> str:
        try:
            return self._backend.generate(request)
        except Exception:  # noqa: BLE001 - a backend failure must not crash the turn
            _LOGGER.warning("backend failed correlation=%s", correlation_id, exc_info=False)
            return "[unavailable] The response backend could not produce an answer."


def _capture_reasons(result: CaptureResult | None) -> tuple[str, ...]:
    if result is None:
        return ("write path failed; degraded",)
    return tuple(op.reason for op in result.operations)


def create_chat_engine(
    config: AiraConfig,
    connection: sqlite3.Connection,
    *,
    backend: GenerationBackend | None = None,
) -> ChatEngine:
    """Wire a chat engine over a config and an open, migrated SQLite connection."""
    repository = MemoryRepository(connection)
    guard = default_guard(max_input_bytes=config.memory.max_record_bytes)
    capture = CaptureService(guard, repository)
    ranker = Ranker(
        RankingWeights.from_config(config.retrieval), DecayParams.from_config(config.decay)
    )
    return ChatEngine(
        capture=capture,
        repository=repository,
        retriever=build_retriever(repository),
        ranker=ranker,
        backend=backend or MockBackend(),
        tokenizer=ByteTokenizer(),
        budget=config.memory.context_token_budget,
        top_k=config.memory.top_k,
    )
