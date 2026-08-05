"""Lifecycle state-machine tests: every allowed and forbidden transition."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

import pytest

from aira.memory.domain import (
    ALLOWED_SOURCES,
    IllegalTransitionError,
    MemoryRecord,
    MemoryStatus,
    Tombstone,
    Transition,
    ValidationError,
    archive_memory,
    can_transition,
    expire_memory,
    forget_memory,
    hard_delete,
    supersede_memory,
    update_memory,
)

Factory = Callable[..., MemoryRecord]

# The five statuses a MemoryRecord can hold (DELETED is a Tombstone, not a record).
RECORD_STATUSES = [
    MemoryStatus.ACTIVE,
    MemoryStatus.SUPERSEDED,
    MemoryStatus.ARCHIVED,
    MemoryStatus.EXPIRED,
    MemoryStatus.FORGOTTEN,
]


def _in_status(make_record: Factory, status: MemoryStatus) -> MemoryRecord:
    """Build a record in the requested status by applying real transitions."""
    rec = make_record()
    if status is MemoryStatus.ACTIVE:
        return rec
    if status is MemoryStatus.SUPERSEDED:
        replacement = make_record(id="mem-2")
        result = supersede_memory(rec, replacement)
        return result.superseded
    if status is MemoryStatus.ARCHIVED:
        state = archive_memory(rec).state
    elif status is MemoryStatus.EXPIRED:
        state = expire_memory(rec).state
    elif status is MemoryStatus.FORGOTTEN:
        state = forget_memory(rec).state
    else:  # pragma: no cover - defensive
        raise AssertionError(status)
    assert isinstance(state, MemoryRecord)
    return state


# --- allowed transitions -----------------------------------------------------------


def test_update_stays_active(make_record: Factory, fixed_now: datetime) -> None:
    rec = make_record()
    later = fixed_now + timedelta(minutes=5)
    result = update_memory(rec, content="owner-a prefers light mode", now=later)
    assert result.transition is Transition.UPDATE
    assert result.to_status is MemoryStatus.ACTIVE
    assert isinstance(result.state, MemoryRecord)
    assert result.state.content == "owner-a prefers light mode"
    assert result.state.updated_at == later


def test_update_requires_a_change(make_record: Factory) -> None:
    with pytest.raises(ValidationError, match="at least one changed field"):
        update_memory(make_record())


def test_archive_expire_forget_targets(make_record: Factory) -> None:
    assert archive_memory(make_record()).to_status is MemoryStatus.ARCHIVED
    assert expire_memory(make_record()).to_status is MemoryStatus.EXPIRED
    assert forget_memory(make_record()).to_status is MemoryStatus.FORGOTTEN


def test_archive_allowed_from_superseded(make_record: Factory) -> None:
    superseded = _in_status(make_record, MemoryStatus.SUPERSEDED)
    result = archive_memory(superseded)
    assert result.to_status is MemoryStatus.ARCHIVED
    assert isinstance(result.state, MemoryRecord)
    # history link is preserved through archival
    assert result.state.superseded_by == "mem-2"


def test_expire_allowed_from_archived(make_record: Factory) -> None:
    archived = _in_status(make_record, MemoryStatus.ARCHIVED)
    assert expire_memory(archived).to_status is MemoryStatus.EXPIRED


def test_forget_allowed_from_all_active_ish(make_record: Factory) -> None:
    for status in (
        MemoryStatus.ACTIVE,
        MemoryStatus.SUPERSEDED,
        MemoryStatus.ARCHIVED,
        MemoryStatus.EXPIRED,
    ):
        rec = _in_status(make_record, status)
        assert forget_memory(rec).to_status is MemoryStatus.FORGOTTEN


# --- superseding -------------------------------------------------------------------


def test_supersede_links_both_records(make_record: Factory) -> None:
    old = make_record(id="mem-1")
    new = make_record(id="mem-2", content="owner-a prefers light mode")
    result = supersede_memory(old, new)
    assert result.superseded.status is MemoryStatus.SUPERSEDED
    assert result.superseded.superseded_by == "mem-2"
    assert result.replacement.status is MemoryStatus.ACTIVE
    assert result.replacement.supersedes == "mem-1"


def test_supersede_requires_same_owner(make_record: Factory) -> None:
    old = make_record(id="mem-1", owner_id="owner-a")
    new = make_record(id="mem-2", owner_id="owner-b")
    with pytest.raises(ValidationError, match="owner"):
        supersede_memory(old, new)


def test_supersede_rejects_self(make_record: Factory) -> None:
    rec = make_record(id="mem-1")
    with pytest.raises(ValidationError, match="itself"):
        supersede_memory(rec, rec)


def test_supersede_requires_active_replacement(make_record: Factory) -> None:
    old = make_record(id="mem-1")
    inactive = _in_status(make_record, MemoryStatus.ARCHIVED)
    with pytest.raises(IllegalTransitionError, match="replacement"):
        supersede_memory(old, inactive)


# --- hard delete -> tombstone ------------------------------------------------------


@pytest.mark.parametrize("status", RECORD_STATUSES)
def test_hard_delete_from_any_status_yields_tombstone(
    make_record: Factory, status: MemoryStatus
) -> None:
    rec = _in_status(make_record, status)
    result = hard_delete(rec, reason="user asked")
    assert result.to_status is MemoryStatus.DELETED
    tomb = result.state
    assert isinstance(tomb, Tombstone)
    assert tomb.id == rec.id
    assert tomb.owner_id == rec.owner_id
    assert not hasattr(tomb, "content")


# --- forbidden transitions ---------------------------------------------------------

SINGLE_RECORD_OPS: list[tuple[Transition, Callable[[MemoryRecord], object]]] = [
    (Transition.UPDATE, lambda r: update_memory(r, content="changed")),
    (Transition.ARCHIVE, archive_memory),
    (Transition.EXPIRE, expire_memory),
    (Transition.FORGET, forget_memory),
    (Transition.HARD_DELETE, hard_delete),
]


@pytest.mark.parametrize("transition,op", SINGLE_RECORD_OPS)
@pytest.mark.parametrize("status", RECORD_STATUSES)
def test_forbidden_transitions_raise(
    make_record: Factory,
    transition: Transition,
    op: Callable[[MemoryRecord], object],
    status: MemoryStatus,
) -> None:
    rec = _in_status(make_record, status)
    allowed = status in ALLOWED_SOURCES[transition]
    if allowed:
        op(rec)  # should not raise
    else:
        with pytest.raises(IllegalTransitionError):
            op(rec)


def test_can_transition_matches_table() -> None:
    for transition, sources in ALLOWED_SOURCES.items():
        for status in MemoryStatus:
            assert can_transition(transition, status) == (status in sources)
