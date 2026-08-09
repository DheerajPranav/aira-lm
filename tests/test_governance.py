"""Tests for Aira Fade (decay/expiry/archival) and governance (user controls)."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from io import StringIO

import pytest

from aira.chat import create_chat_engine, run_session
from aira.config import load_config
from aira.memory.domain.enums import MemoryKind, ProvenanceSource, RetentionPolicy
from aira.memory.domain.records import MemoryRecord, Provenance, make_memory
from aira.memory.fade import FadeJob, decay_score
from aira.memory.governance import GovernanceError, GovernanceService, ImportRejectedError
from aira.memory.guard import default_guard
from aira.memory.recall import build_retriever
from aira.memory.trail import AuditAction
from aira.memory.vault import MemoryRepository, connect

OLD = datetime(2020, 1, 1, tzinfo=UTC)
NOW = datetime(2026, 1, 1, tzinfo=UTC)
RECENT = NOW - timedelta(days=1)
OWNER = "owner-a"
_CFG = load_config("configs/aira_tiny.toml")
_PROV = Provenance(
    source=ProvenanceSource.USER_EXPLICIT, actor=OWNER, method="test", captured_at=OLD
)


def _add(
    repo: MemoryRepository,
    mid: str,
    content: str = "the version of tool orion is 3.2",
    *,
    owner: str = OWNER,
    kind: MemoryKind = MemoryKind.SEMANTIC,
    created: datetime = NOW,
    retention: RetentionPolicy = RetentionPolicy.DURABLE_UNTIL_DELETION,
    expires_at: datetime | None = None,
) -> MemoryRecord:
    return repo.create(
        make_memory(
            id=mid,
            owner_id=owner,
            content=content,
            kind=kind,
            provenance=Provenance(
                source=ProvenanceSource.USER_EXPLICIT,
                actor=owner,
                method="test",
                captured_at=created,
            ),
            now=created,
            retention=retention,
            expires_at=expires_at,
        )
    )


@pytest.fixture
def repo() -> MemoryRepository:
    return MemoryRepository(connect(":memory:"))


@pytest.fixture
def gov(repo: MemoryRepository) -> GovernanceService:
    counter = {"n": 0}

    def new_id() -> str:
        counter["n"] += 1
        return f"c{counter['n']}"

    return GovernanceService(repo, default_guard(), new_id=new_id)


def _fade(repo: MemoryRepository) -> FadeJob:
    return FadeJob(repo, _CFG.decay)


# --- decay -------------------------------------------------------------------------


def test_decay_is_fixed_clock(repo: MemoryRepository) -> None:
    rec = _add(repo, "m1", created=RECENT)
    a = decay_score(rec, NOW, _CFG.decay)
    b = decay_score(rec, NOW, _CFG.decay)
    assert a == b
    assert 0.0 < a <= 1.0


def test_kind_specific_decay_rates(repo: MemoryRepository) -> None:
    created = NOW - timedelta(days=100)
    episodic = _add(repo, "e", kind=MemoryKind.EPISODIC, created=created)
    instruction = _add(repo, "i", kind=MemoryKind.INSTRUCTION, created=created)
    # instructions decay far slower than episodic memories
    assert decay_score(episodic, NOW, _CFG.decay) < decay_score(instruction, NOW, _CFG.decay)


# --- reinforcement (separate from retrieval) ---------------------------------------


def test_retrieval_does_not_reinforce(repo: MemoryRepository) -> None:
    _add(repo, "m1", content="orion version fact", created=RECENT)
    build_retriever(repo).search(OWNER, "orion", limit=5)
    assert repo.get(OWNER, "m1").reinforcement_count == 0  # type: ignore[union-attr]


def test_explicit_reinforcement(gov: GovernanceService, repo: MemoryRepository) -> None:
    _add(repo, "m1", created=RECENT)
    updated = gov.reinforce(OWNER, "m1", now=NOW)
    assert updated.reinforcement_count == 1
    actions = [e.action for e in repo.audit_events_for(OWNER, "m1")]
    assert AuditAction.REINFORCE in actions


# --- fade job ----------------------------------------------------------------------


def test_archive_below_threshold(repo: MemoryRepository) -> None:
    _add(repo, "stale", kind=MemoryKind.EPISODIC, created=OLD)  # very old -> tiny decay score
    _add(repo, "fresh", kind=MemoryKind.SEMANTIC, created=RECENT)
    report = _fade(repo).run(now=NOW)
    assert "stale" in report.archived
    assert {m.id for m in repo.list_memories(OWNER)} == {"fresh"}


def test_expiry_by_retention(repo: MemoryRepository) -> None:
    _add(repo, "fx", created=OLD, retention=RetentionPolicy.FIXED_EXPIRY, expires_at=OLD)
    _add(repo, "ses", created=RECENT, retention=RetentionPolicy.SESSION_ONLY)
    report = _fade(repo).run(now=NOW)
    assert set(report.expired) == {"fx", "ses"}
    assert repo.list_memories(OWNER) == []


def test_fade_never_hard_deletes(repo: MemoryRepository) -> None:
    _add(repo, "stale", kind=MemoryKind.EPISODIC, created=OLD)
    _fade(repo).run(now=NOW)
    # the memory still exists (archived), and nothing was hard-deleted
    assert repo.get(OWNER, "stale", include_inactive=True) is not None
    actions = [e.action for e in repo.audit_events_for(OWNER, "stale")]
    assert AuditAction.HARD_DELETE not in actions


# --- inspect / explain / correct ---------------------------------------------------


def test_inspect_and_explain(gov: GovernanceService, repo: MemoryRepository) -> None:
    _add(repo, "m1", created=RECENT)
    assert [m.id for m in gov.inspect_all(OWNER)] == ["m1"]
    explanation = gov.explain(OWNER, "m1")
    assert explanation.memory is not None
    assert AuditAction.CREATE in {e.action for e in explanation.events}


def test_correction_supersedes(gov: GovernanceService, repo: MemoryRepository) -> None:
    _add(repo, "m1", content="my editor is vim", kind=MemoryKind.PREFERENCE, created=RECENT)
    replacement = gov.correct(OWNER, "m1", "my editor is neovim", now=NOW)
    assert replacement.content == "my editor is neovim"
    assert replacement.provenance.source is ProvenanceSource.USER_CORRECTION
    assert {m.id for m in gov.inspect_all(OWNER)} == {replacement.id}


def test_correction_blocked_by_guard(gov: GovernanceService, repo: MemoryRepository) -> None:
    _add(repo, "m1", created=RECENT)
    with pytest.raises(GovernanceError, match="guard"):
        gov.correct(OWNER, "m1", "my key is AKIAIOSFODNN7EXAMPLE", now=NOW)


# --- export / import ---------------------------------------------------------------


def test_export_excludes_forbidden_by_default(
    gov: GovernanceService, repo: MemoryRepository
) -> None:
    _add(repo, "keep", content="orion version", created=RECENT)
    _add(repo, "gone", content="falcon project", created=RECENT)
    repo.forget(OWNER, "gone", now=NOW)
    default = gov.export(OWNER)
    assert "orion" in default
    assert "falcon" not in default
    assert "falcon" in gov.export(OWNER, include_inactive=True)


def test_malformed_import_writes_nothing(gov: GovernanceService, repo: MemoryRepository) -> None:
    bad = json.dumps({"schema_version": 1, "content": "hi"})  # missing required fields
    with pytest.raises(ImportRejectedError):
        gov.import_("owner-b", bad)
    assert repo.list_memories("owner-b") == []


# --- delete-all --------------------------------------------------------------------


def test_delete_all_is_owner_scoped(gov: GovernanceService, repo: MemoryRepository) -> None:
    _add(repo, "a1", owner="owner-a", created=RECENT)
    _add(repo, "a2", owner="owner-a", content="second", created=RECENT)
    _add(repo, "b1", owner="owner-b", created=RECENT)
    count = gov.delete_all("owner-a", now=NOW)
    assert count == 2
    assert repo.list_memories("owner-a") == []
    assert len(repo.list_memories("owner-b")) == 1


# --- CLI session governance --------------------------------------------------------


def test_session_governance_smoke() -> None:
    engine = create_chat_engine(_CFG, connect(":memory:"))
    now_factory: Callable[[], datetime] = lambda: NOW  # noqa: E731
    out = StringIO()
    run_session(
        engine,
        OWNER,
        ["my editor is vim", "/fade", "/delete-all", "/memories"],
        out,
        now_factory=now_factory,
    )
    text = out.getvalue()
    assert "fade:" in text
    assert "deleted" in text
    assert "(no memories)" in text
