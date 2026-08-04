"""Shared test fixtures, including a default no-network guard.

Aira's runtime and tests must not make network calls. This guard blocks outbound
socket connections for every test unless the test is explicitly marked
``@pytest.mark.network``. It is a safety net, not a substitute for keeping the code
offline by design.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator
from typing import Any

import pytest


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
