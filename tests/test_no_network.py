"""Verify the default no-network guard blocks outbound connections.

``NetworkBlockedError`` subclasses ``RuntimeError``; matching on the base class keeps
this test independent of how conftest is imported.
"""

from __future__ import annotations

import socket

import pytest


def test_connect_is_blocked_by_default() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="network access is blocked"):
            s.connect(("127.0.0.1", 9))
    finally:
        s.close()


def test_connect_ex_is_blocked_by_default() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="network access is blocked"):
            s.connect_ex(("127.0.0.1", 9))
    finally:
        s.close()
