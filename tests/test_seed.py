"""Determinism tests for the seeding utility."""

from __future__ import annotations

import random

import pytest

from aira.seed import set_seed


def test_same_seed_same_sequence() -> None:
    set_seed(123)
    a = [random.random() for _ in range(5)]
    set_seed(123)
    b = [random.random() for _ in range(5)]
    assert a == b


def test_different_seed_differs() -> None:
    set_seed(1)
    a = [random.random() for _ in range(5)]
    set_seed(2)
    b = [random.random() for _ in range(5)]
    assert a != b


def test_returns_seed() -> None:
    assert set_seed(7) == 7


def test_negative_seed_rejected() -> None:
    with pytest.raises(ValueError, match="seed must be >= 0"):
        set_seed(-5)
