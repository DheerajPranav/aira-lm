"""Shared test fixtures, including a default no-network guard.

Aira's runtime and tests must not make network calls. This guard blocks outbound
socket connections for every test unless the test is explicitly marked
``@pytest.mark.network``. It is a safety net, not a substitute for keeping the code
offline by design.
"""

from __future__ import annotations

import socket
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

from aira.memory.domain import (
    MemoryKind,
    MemoryRecord,
    Provenance,
    ProvenanceSource,
    make_memory,
)


class NetworkBlockedError(RuntimeError):
    """Raised when a test attempts a network connection without the ``network`` marker."""


@pytest.fixture(autouse=True)
def _no_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Block outbound socket connections unless the test is marked ``network``."""
    if request.node.get_closest_marker("network") is not None:
        yield
        return

    def _blocked(*_args: Any, **_kwargs: Any) -> None:
        raise NetworkBlockedError(
            "network access is blocked in tests; mark with @pytest.mark.network to allow"
        )

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    yield


# --- Domain test fixtures (fixed clock for determinism) ---------------------------

FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_now() -> datetime:
    """A fixed, timezone-aware UTC instant for deterministic timestamps."""
    return FIXED_NOW


@pytest.fixture
def provenance() -> Provenance:
    """An explicit-user provenance captured at the fixed instant."""
    return Provenance(
        source=ProvenanceSource.USER_EXPLICIT,
        actor="owner-a",
        method="explicit remember request",
        captured_at=FIXED_NOW,
    )


@pytest.fixture
def make_record(provenance: Provenance) -> Callable[..., MemoryRecord]:
    """Return a factory that builds ACTIVE memory records with sensible defaults."""

    def _factory(
        *,
        id: str = "mem-1",
        owner_id: str = "owner-a",
        content: str = "owner-a prefers dark mode",
        kind: MemoryKind = MemoryKind.PREFERENCE,
        **kwargs: Any,
    ) -> MemoryRecord:
        return make_memory(
            id=id,
            owner_id=owner_id,
            content=content,
            kind=kind,
            provenance=provenance,
            now=FIXED_NOW,
            **kwargs,
        )

    return _factory
