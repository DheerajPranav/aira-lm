"""Smoke test: every package namespace imports cleanly."""

from __future__ import annotations

import importlib

import pytest

MODULES = [
    "aira",
    "aira.config",
    "aira.seed",
    "aira.device",
    "aira.cli",
    "aira.cli.main",
    "aira.core",
    "aira.memory",
    "aira.chat",
    "aira.evaluation",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name: str) -> None:
    assert importlib.import_module(name) is not None


def test_version_present() -> None:
    import aira

    assert isinstance(aira.__version__, str)
    assert aira.__version__
