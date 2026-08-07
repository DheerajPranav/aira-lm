"""Tests for Aira Recall: keyword retrieval, owner/lifecycle scoping, determinism."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from aira.memory.domain.enums import MemoryKind, ProvenanceSource
from aira.memory.domain.records import MemoryRecord, Provenance, make_memory
from aira.memory.recall import (
    Bm25Retriever,
    Fts5Retriever,
    RetrievalFilters,
    Retriever,
    build_retriever,
)
from aira.memory.vault import MemoryRepository, connect

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
OWNER = "owner-a"

_PROV = Provenance(
    source=ProvenanceSource.USER_EXPLICIT,
    actor=OWNER,
    method="test",
    captured_at=NOW,
)

Adder = Callable[..., MemoryRecord]


@pytest.fixture
def seeded() -> MemoryRepository:
    repo = MemoryRepository(connect(":memory:"))

    def add(
        mid: str,
        content: str,
        *,
        owner: str = OWNER,
        kind: MemoryKind = MemoryKind.SEMANTIC,
        **kw: object,
    ) -> None:
        repo.create(
            make_memory(
                id=mid, owner_id=owner, content=content, kind=kind, provenance=_PROV, now=NOW, **kw
            )
        )

    add("m1", "the version of tool orion is 3.2")
    add("m2", "owner-a prefers dark mode", kind=MemoryKind.PREFERENCE)
    add("m3", "owner-a is working on project falcon", project="falcon")
    add("m4", "the capital of country zeta is qux")
    add("b1", "owner-b secret deployment plan", owner="owner-b")
    return repo


@pytest.fixture(params=["bm25", "fts5"])
def retriever(request: pytest.FixtureRequest, seeded: MemoryRepository) -> Retriever:
    if request.param == "bm25":
        return Bm25Retriever(seeded)
    return Fts5Retriever(seeded)


# --- core retrieval ----------------------------------------------------------------


def test_exact_string_retrieval(retriever: Retriever) -> None:
    results = retriever.search(OWNER, "orion")
    assert results
    assert results[0].memory.id == "m1"
    assert results[0].score > 0


def test_keyword_ranking(retriever: Retriever) -> None:
    assert retriever.search(OWNER, "dark mode")[0].memory.id == "m2"
    assert retriever.search(OWNER, "project falcon")[0].memory.id == "m3"


def test_results_are_explainable(retriever: Retriever) -> None:
    result = retriever.search(OWNER, "orion")[0]
    assert "backend" in result.explanation


def test_satisfies_protocol(retriever: Retriever) -> None:
    assert isinstance(retriever, Retriever)


# --- owner isolation (invariant 1) -------------------------------------------------


def test_owner_isolation(retriever: Retriever) -> None:
    # owner-a can never see owner-b's memory
    assert retriever.search(OWNER, "deployment plan") == []
    # owner-b sees only their own
    other = retriever.search("owner-b", "deployment")
    assert other and all(r.memory.owner_id == "owner-b" for r in other)


# --- lifecycle exclusion (invariant 2) ---------------------------------------------


def test_forgotten_excluded(retriever: Retriever, seeded: MemoryRepository) -> None:
    seeded.forget(OWNER, "m2", now=LATER)
    assert all(r.memory.id != "m2" for r in retriever.search(OWNER, "dark mode"))


def test_expired_excluded(retriever: Retriever, seeded: MemoryRepository) -> None:
    seeded.expire(OWNER, "m4", now=LATER)
    assert retriever.search(OWNER, "capital zeta") == []


def test_superseded_excluded(retriever: Retriever, seeded: MemoryRepository) -> None:
    replacement = make_memory(
        id="m1b",
        owner_id=OWNER,
        content="the version of tool orion is 4.0",
        kind=MemoryKind.SEMANTIC,
        provenance=_PROV,
        now=LATER,
    )
    seeded.supersede(OWNER, "m1", replacement, now=LATER)
    results = retriever.search(OWNER, "orion")
    ids = {r.memory.id for r in results}
    assert "m1" not in ids
    assert "m1b" in ids


def test_hard_delete_removes_searchable_content(
    retriever: Retriever, seeded: MemoryRepository
) -> None:
    seeded.hard_delete(OWNER, "m1", now=LATER)
    assert retriever.search(OWNER, "orion") == []


def test_index_updates_after_correction(retriever: Retriever, seeded: MemoryRepository) -> None:
    seeded.update(OWNER, "m2", content="owner-a prefers light mode", now=LATER)
    assert retriever.search(OWNER, "dark") == []
    assert any(r.memory.id == "m2" for r in retriever.search(OWNER, "light"))


# --- filters -----------------------------------------------------------------------


def test_kind_filter(retriever: Retriever) -> None:
    results = retriever.search(OWNER, "owner", filters=RetrievalFilters(kind=MemoryKind.PREFERENCE))
    assert results and all(r.memory.kind is MemoryKind.PREFERENCE for r in results)


def test_project_filter(retriever: Retriever) -> None:
    results = retriever.search(OWNER, "owner", filters=RetrievalFilters(project="falcon"))
    assert results and all(r.memory.project == "falcon" for r in results)


# --- query edge cases --------------------------------------------------------------


def test_empty_query(retriever: Retriever) -> None:
    assert retriever.search(OWNER, "") == []
    assert retriever.search(OWNER, "   ") == []


def test_malformed_query_is_safe(retriever: Retriever) -> None:
    # FTS operator characters / quotes must not raise or inject.
    for bad in ['orion AND "((', '"; DROP TABLE memories; --', "* OR *", "()"]:
        result = retriever.search(OWNER, bad)
        assert isinstance(result, list)


def test_zero_limit(retriever: Retriever) -> None:
    assert retriever.search(OWNER, "orion", limit=0) == []


# --- determinism -------------------------------------------------------------------


def test_deterministic(retriever: Retriever) -> None:
    a = retriever.search(OWNER, "owner-a")
    b = retriever.search(OWNER, "owner-a")
    assert [r.memory.id for r in a] == [r.memory.id for r in b]


# --- backend selection + FTS index hygiene -----------------------------------------


def test_build_retriever_prefers_fts(seeded: MemoryRepository) -> None:
    # FTS5 is available on the test environment.
    assert isinstance(build_retriever(seeded), Fts5Retriever)


def test_fts_table_purged_on_hard_delete(seeded: MemoryRepository) -> None:
    seeded.hard_delete(OWNER, "m1", now=LATER)
    remaining = seeded.fts_search('"orion"', limit=10)
    assert all(mid != "m1" for mid, _ in remaining)


# --- latency benchmark -------------------------------------------------------------


def test_retrieval_latency(seeded: MemoryRepository) -> None:
    for i in range(300):
        seeded.create(
            make_memory(
                id=f"x{i}",
                owner_id=OWNER,
                content=f"note number {i} about orion and falcon deployments",
                kind=MemoryKind.SEMANTIC,
                provenance=_PROV,
                now=NOW,
            )
        )
    retriever = build_retriever(seeded)
    start = time.perf_counter()
    results = retriever.search(OWNER, "orion falcon", limit=5)
    elapsed = time.perf_counter() - start
    assert results
    assert elapsed < 2.0  # generous local bound
