"""Tests for the capture (write-path) pipeline: extraction, evaluation, resolution."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from aira.memory.capture import (
    CaptureService,
    ForgetOp,
    IgnoreOp,
    RememberOp,
    Speaker,
    SupersedeOp,
)
from aira.memory.domain.enums import MemoryKind, ProvenanceSource
from aira.memory.guard import default_guard
from aira.memory.vault import MemoryRepository, connect

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
OWNER = "owner-a"


def _id_factory() -> Callable[[], str]:
    counter = {"n": 0}

    def factory() -> str:
        counter["n"] += 1
        return f"m{counter['n']}"

    return factory


@pytest.fixture
def service_and_repo() -> tuple[CaptureService, MemoryRepository]:
    repo = MemoryRepository(connect(":memory:"))
    return CaptureService(default_guard(), repo, new_id=_id_factory()), repo


# --- admission scenarios -----------------------------------------------------------


def test_explicit_remember(service_and_repo: tuple[CaptureService, MemoryRepository]) -> None:
    service, repo = service_and_repo
    result = service.process(OWNER, Speaker.USER, "remember that my role is engineer", now=NOW)
    assert len(result.of_type(RememberOp)) == 1
    stored = repo.list_memories(OWNER)
    assert len(stored) == 1
    assert stored[0].kind is MemoryKind.SEMANTIC
    assert stored[0].provenance.source is ProvenanceSource.USER_EXPLICIT


def test_preference(service_and_repo: tuple[CaptureService, MemoryRepository]) -> None:
    service, repo = service_and_repo
    service.process(OWNER, Speaker.USER, "I prefer dark mode", now=NOW)
    stored = repo.list_memories(OWNER)
    assert len(stored) == 1
    assert stored[0].kind is MemoryKind.PREFERENCE


def test_project_fact(service_and_repo: tuple[CaptureService, MemoryRepository]) -> None:
    service, repo = service_and_repo
    service.process(OWNER, Speaker.USER, "I'm working on project falcon", now=NOW)
    stored = repo.list_memories(OWNER)
    assert len(stored) == 1
    assert stored[0].project == "falcon"


def test_do_not_remember_is_ignored(
    service_and_repo: tuple[CaptureService, MemoryRepository],
) -> None:
    service, repo = service_and_repo
    result = service.process(
        OWNER, Speaker.USER, "please don't remember this, it's just temporary", now=NOW
    )
    assert result.of_type(IgnoreOp)
    assert not result.stored_anything
    assert repo.list_memories(OWNER) == []


def test_temporary_low_value_dropped(
    service_and_repo: tuple[CaptureService, MemoryRepository],
) -> None:
    service, repo = service_and_repo
    result = service.process(OWNER, Speaker.USER, "my editor is vim for now", now=NOW)
    assert result.of_type(IgnoreOp)
    assert repo.list_memories(OWNER) == []


def test_assistant_statement_not_promoted(
    service_and_repo: tuple[CaptureService, MemoryRepository],
) -> None:
    service, repo = service_and_repo
    result = service.process(OWNER, Speaker.ASSISTANT, "my editor is vim", now=NOW)
    assert result.of_type(IgnoreOp)
    assert repo.list_memories(OWNER) == []


def test_unsafe_candidate_blocked(
    service_and_repo: tuple[CaptureService, MemoryRepository],
) -> None:
    service, repo = service_and_repo
    result = service.process(
        OWNER, Speaker.USER, "please remember AKIAIOSFODNN7EXAMPLE for later", now=NOW
    )
    assert result.blocked
    assert repo.list_memories(OWNER) == []
    # the secret never reaches storage or the trace's redacted preview
    assert "AKIAIOSFODNN7EXAMPLE" not in result.guard.redacted_preview


def test_correction_supersedes(
    service_and_repo: tuple[CaptureService, MemoryRepository],
) -> None:
    service, repo = service_and_repo
    service.process(OWNER, Speaker.USER, "my editor is vim", now=NOW)
    result = service.process(OWNER, Speaker.USER, "actually, my editor is neovim", now=LATER)

    assert len(result.of_type(SupersedeOp)) == 1
    active = repo.list_memories(OWNER)
    assert len(active) == 1
    assert active[0].content == "my editor is neovim"
    assert active[0].provenance.source is ProvenanceSource.USER_CORRECTION


def test_ambiguous_correction_ignored(
    service_and_repo: tuple[CaptureService, MemoryRepository],
) -> None:
    service, repo = service_and_repo
    result = service.process(OWNER, Speaker.USER, "actually, never mind", now=NOW)
    assert result.of_type(IgnoreOp)
    assert "ambiguous" in result.operations[0].reason  # type: ignore[union-attr]
    assert repo.list_memories(OWNER) == []


def test_duplicate_ignored(service_and_repo: tuple[CaptureService, MemoryRepository]) -> None:
    service, repo = service_and_repo
    service.process(OWNER, Speaker.USER, "my role is engineer", now=NOW)
    result = service.process(OWNER, Speaker.USER, "my role is engineer", now=LATER)
    assert result.of_type(IgnoreOp)
    assert len(repo.list_memories(OWNER)) == 1


def test_forget_existing(service_and_repo: tuple[CaptureService, MemoryRepository]) -> None:
    service, repo = service_and_repo
    service.process(OWNER, Speaker.USER, "my editor is vim", now=NOW)
    result = service.process(OWNER, Speaker.USER, "forget my editor", now=LATER)
    assert len(result.of_type(ForgetOp)) == 1
    assert repo.list_memories(OWNER) == []


def test_forget_nothing_is_ignored(
    service_and_repo: tuple[CaptureService, MemoryRepository],
) -> None:
    service, repo = service_and_repo
    result = service.process(OWNER, Speaker.USER, "forget my editor", now=NOW)
    assert result.of_type(IgnoreOp)
    assert repo.list_memories(OWNER) == []


# --- provenance / evidence ---------------------------------------------------------


def test_provenance_recorded(service_and_repo: tuple[CaptureService, MemoryRepository]) -> None:
    service, repo = service_and_repo
    service.process(OWNER, Speaker.USER, "my role is engineer", now=NOW)
    record = repo.list_memories(OWNER)[0]
    assert record.provenance.actor == OWNER
    assert record.provenance.method
    assert record.provenance.captured_at == NOW
    assert record.provenance.source_excerpt


def test_explicit_has_stronger_evidence_than_inferred() -> None:
    repo = MemoryRepository(connect(":memory:"))
    service = CaptureService(default_guard(), repo, new_id=_id_factory())
    explicit = service.process(OWNER, Speaker.USER, "remember that my role is engineer", now=NOW)
    inferred = service.process("owner-b", Speaker.USER, "my role is engineer", now=NOW)
    exp_conf = explicit.of_type(RememberOp)[0].record.confidence  # type: ignore[union-attr]
    inf_conf = inferred.of_type(RememberOp)[0].record.confidence  # type: ignore[union-attr]
    assert exp_conf > inf_conf


# --- policy trace ------------------------------------------------------------------


def test_policy_trace_present(service_and_repo: tuple[CaptureService, MemoryRepository]) -> None:
    service, _repo = service_and_repo
    result = service.capture(OWNER, Speaker.USER, "my role is engineer", now=NOW, debug=True)
    stages = {entry.stage for entry in result.trace}
    assert {"guard", "extract", "evaluate", "resolve"} <= stages
