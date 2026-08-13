"""Tests for memory-conditioned evaluation and the Aira Core chat integration."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aira.chat import ChatEngine, create_chat_engine
from aira.config import ModelConfig, load_config
from aira.core import AiraCore, TinyTransformerBackend, build_model
from aira.evaluation import MemoryConditionedEvaluator, MemoryEvalReport, default_memory_tasks
from aira.memory.vault import connect

_CFG = load_config("configs/aira_tiny.toml")
_SMALL = ModelConfig(
    vocab_size=256,
    context_length=64,
    embedding_dim=64,
    layers=2,
    heads=4,
    ffn_multiplier=4,
    dropout=0.0,
    tie_embeddings=True,
)


def _small_model() -> AiraCore:
    return build_model(_SMALL, seed=0)


@pytest.fixture(scope="module")
def report() -> MemoryEvalReport:
    evaluator = MemoryConditionedEvaluator(_CFG, _small_model(), seed=0, max_new_tokens=4)
    return evaluator.run()


# --- backend adapter integration ---------------------------------------------------


def test_tiny_backend_integrates_with_chat() -> None:
    engine: ChatEngine = create_chat_engine(
        _CFG, connect(":memory:"), backend=TinyTransformerBackend(_small_model(), device="cpu")
    )
    response = engine.chat("owner-a", "hello there", now=datetime(2026, 1, 1, tzinfo=UTC))
    assert isinstance(response.text, str)
    assert response.text  # the tiny model produces (meaningless) text
    assert not response.degraded


# --- baselines ---------------------------------------------------------------------


def test_three_baselines_present(report: MemoryEvalReport) -> None:
    assert set(report.baselines) == {"no_memory", "aira", "full_history"}
    assert report.task_count == len(default_memory_tasks())


def test_memory_improves_context_availability(report: MemoryEvalReport) -> None:
    # Retrieval places the fact in context; no-memory cannot.
    assert report.baselines["no_memory"].context_availability == 0.0
    assert report.baselines["aira"].context_availability == 1.0
    assert report.baselines["full_history"].context_availability == 1.0


def test_generation_adherence_reported_honestly(report: MemoryEvalReport) -> None:
    # The untrained tiny model is not expected to reproduce facts; this is reported, not hidden.
    assert report.baselines["aira"].generation_adherence == 0.0
    assert "inconclusive" in report.conclusion.lower() or "training" in report.conclusion.lower()


def test_forgotten_is_never_disclosed(report: MemoryEvalReport) -> None:
    for name in ("no_memory", "aira", "full_history"):
        assert report.baselines[name].forgotten_nondisclosure == 1.0


def test_aira_context_within_budget(report: MemoryEvalReport) -> None:
    assert report.baselines["aira"].avg_context_tokens <= _CFG.memory.context_token_budget


# --- ablation, versions, reproducibility, report -----------------------------------


def test_ablation_present(report: MemoryEvalReport) -> None:
    assert set(report.ablation) == {"default_ranking", "lexical_only"}


def test_model_versions_recorded(report: MemoryEvalReport) -> None:
    assert report.model["parameter_count"] > 0
    assert report.model["checkpoint"] is None
    assert "seed" in report.model


def test_report_is_reproducible() -> None:
    a = MemoryConditionedEvaluator(_CFG, _small_model(), seed=0, max_new_tokens=4).run()
    b = MemoryConditionedEvaluator(_CFG, _small_model(), seed=0, max_new_tokens=4).run()
    assert a.canonical() == b.canonical()


def test_report_renders(report: MemoryEvalReport) -> None:
    markdown = report.to_markdown()
    assert "Memory-Conditioned Evaluation" in markdown
    assert "Conclusion" in markdown
    data = report.to_dict()
    assert "baselines" in data
    assert "latency_ms" in data
