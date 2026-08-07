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
    "aira.memory.domain",
    "aira.memory.domain.enums",
    "aira.memory.domain.records",
    "aira.memory.domain.lifecycle",
    "aira.memory.domain.hashing",
    "aira.memory.domain.clock",
    "aira.memory.domain.errors",
    "aira.memory.guard",
    "aira.memory.guard.interface",
    "aira.memory.guard.detectors",
    "aira.memory.guard.redaction",
    "aira.memory.guard.guard",
    "aira.memory.trail",
    "aira.memory.trail.events",
    "aira.memory.vault",
    "aira.memory.vault.schema",
    "aira.memory.vault.connection",
    "aira.memory.vault.mapper",
    "aira.memory.vault.repository",
    "aira.memory.vault.backup",
    "aira.memory.capture",
    "aira.memory.capture.models",
    "aira.memory.capture.extraction",
    "aira.memory.capture.evaluation",
    "aira.memory.capture.service",
    "aira.memory.recall",
    "aira.memory.recall.models",
    "aira.memory.recall.tokenize",
    "aira.memory.recall.interface",
    "aira.memory.recall.bm25",
    "aira.memory.recall.fts",
    "aira.memory.recall.factory",
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
