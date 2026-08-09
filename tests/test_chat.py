"""End-to-end chat tests: full lifecycle through the mock backend + degradation."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from io import StringIO
from typing import Any

import pytest

from aira.chat import (
    ChatEngine,
    GenerationBackend,
    MockBackend,
    create_chat_engine,
    run_session,
)
from aira.config import load_config
from aira.memory.vault import connect

NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
LATER2 = NOW + timedelta(hours=2)
OWNER = "owner-a"

_CFG = load_config("configs/aira_tiny.toml")


@pytest.fixture
def engine() -> ChatEngine:
    return create_chat_engine(_CFG, connect(":memory:"))


# --- end-to-end lifecycle ----------------------------------------------------------


def test_remember_then_recall(engine: ChatEngine) -> None:
    engine.chat(OWNER, "my editor is vim", now=NOW)
    response = engine.chat(OWNER, "what is my editor?", now=LATER)
    assert response.memory_used
    assert not response.degraded
    assert "vim" in response.text


def test_correction_then_recall(engine: ChatEngine) -> None:
    engine.chat(OWNER, "my editor is vim", now=NOW)
    engine.chat(OWNER, "actually, my editor is neovim", now=LATER)
    response = engine.chat(OWNER, "what is my editor?", now=LATER2)
    active = engine.memories(OWNER)
    assert len(active) == 1
    assert active[0].content == "my editor is neovim"
    assert "neovim" in response.text


def test_forget_then_non_recall(engine: ChatEngine) -> None:
    engine.chat(OWNER, "my editor is vim", now=NOW)
    engine.chat(OWNER, "forget my editor", now=LATER)
    response = engine.chat(OWNER, "what is my editor?", now=LATER2)
    assert not response.memory_used
    assert "vim" not in response.text
    assert "no relevant memory" in response.text.lower()


def test_unsafe_write_is_blocked(engine: ChatEngine) -> None:
    response = engine.chat(OWNER, "please remember AKIAIOSFODNN7EXAMPLE", now=NOW)
    assert isinstance(response.text, str)  # still answered
    assert engine.memories(OWNER) == []  # nothing stored
    assert not response.memory_used


def test_owner_isolation_through_chat(engine: ChatEngine) -> None:
    engine.chat("owner-a", "my editor is vim", now=NOW)
    response = engine.chat("owner-b", "what is my editor?", now=LATER)
    assert not response.memory_used
    assert "vim" not in response.text


# --- graceful degradation (invariant 3) --------------------------------------------


class _BoomRetriever:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def search(self, owner_id: str, query: str, *, filters: Any = None, limit: int = 5) -> Any:
        raise self._exc


@pytest.mark.parametrize(
    "exc",
    [TimeoutError("retrieval slow"), sqlite3.OperationalError("db gone"), ValueError("bad row")],
    ids=["timeout", "db-unavailable", "malformed-memory"],
)
def test_retrieval_failure_degrades(
    engine: ChatEngine, exc: Exception, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(engine, "_retriever", _BoomRetriever(exc))
    response = engine.chat(OWNER, "what is my editor?", now=NOW)
    assert response.degraded
    assert not response.memory_used
    assert response.text  # a response is still produced


def test_write_failure_degrades(engine: ChatEngine, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a: object, **_k: object) -> Any:
        raise RuntimeError("capture exploded")

    monkeypatch.setattr(engine._capture, "process", boom)
    response = engine.chat(OWNER, "my editor is vim", now=NOW)
    assert response.degraded
    assert response.text


# --- debug + observability ---------------------------------------------------------


def test_debug_off_hides_internals(engine: ChatEngine) -> None:
    engine.chat(OWNER, "my editor is vim", now=NOW)
    response = engine.chat(OWNER, "what is my editor?", now=LATER, debug=False)
    assert response.debug is None
    assert "id=" not in response.text


def test_debug_on_exposes_metadata(engine: ChatEngine) -> None:
    engine.chat(OWNER, "my editor is vim", now=NOW, debug=True)
    response = engine.chat(OWNER, "what is my editor?", now=LATER, debug=True)
    assert response.debug is not None
    assert response.debug.included_memory_ids
    assert "<untrusted_memory>" in response.debug.memory_block


def test_latency_and_correlation_present(engine: ChatEngine) -> None:
    response = engine.chat(OWNER, "hello", now=NOW)
    assert isinstance(response.latency_ms, float)
    assert response.latency_ms >= 0
    assert response.correlation_id


def test_mock_backend_is_a_backend() -> None:
    assert isinstance(MockBackend(), GenerationBackend)


# --- CLI session -------------------------------------------------------------------


def test_session_smoke(engine: ChatEngine) -> None:
    lines = [
        "my editor is vim",
        "/memories",
        "what is my editor?",
        "/stats",
        "/exit",
        "this line is ignored after exit",
    ]
    out = StringIO()
    stats = run_session(engine, OWNER, lines, out, now_factory=lambda: NOW)
    text = out.getvalue()
    assert "vim" in text  # listed and recalled
    assert "messages=" in text
    assert stats.messages == 2  # two chat turns (the memories/stats lines are commands)


def test_session_forget_command(engine: ChatEngine) -> None:
    engine.chat(OWNER, "my editor is vim", now=NOW)
    memory_id = engine.memories(OWNER)[0].id
    out = StringIO()
    run_session(
        engine, OWNER, [f"/forget {memory_id}", "/memories"], out, now_factory=lambda: LATER
    )
    text = out.getvalue()
    assert "forgotten" in text
    assert "(no memories)" in text


def test_session_debug_toggle(engine: ChatEngine) -> None:
    out = StringIO()
    run_session(
        engine, OWNER, ["/debug", "my editor is vim", "/exit"], out, now_factory=lambda: NOW
    )
    text = out.getvalue()
    assert "debug on" in text
    assert "correlation=" in text
