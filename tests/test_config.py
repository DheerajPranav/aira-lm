"""Configuration loading and validation tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from aira.config import AiraConfig, ConfigError, load_config

REPO_DEFAULT = Path("configs/aira_tiny.toml")


def test_loads_repo_default() -> None:
    cfg = load_config(REPO_DEFAULT)
    assert isinstance(cfg, AiraConfig)
    assert cfg.project.name == "aira-lm"
    assert cfg.model.vocab_size == 256
    assert cfg.runtime.offline is True
    assert cfg.retrieval.backend in {"auto", "fts5", "bm25"}


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.toml")


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "cfg.toml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


MINIMAL = """
    [project]
    name = "x"
    tagline = "y"
    [model]
    vocab_size = 256
    context_length = 512
    embedding_dim = 256
    layers = 8
    heads = 8
    ffn_multiplier = 4
    dropout = 0.1
    tie_embeddings = true
    [generation]
    max_new_tokens = 128
    temperature = 0.8
    top_k = 40
    [memory]
    default_owner_id = "local-user"
    max_record_bytes = 8192
    context_token_budget = 256
    top_k = 5
    [retrieval]
    backend = "auto"
    lexical_weight = 0.4
    importance_weight = 0.15
    confidence_weight = 0.15
    recency_weight = 0.1
    reinforcement_weight = 0.05
    project_weight = 0.1
    kind_weight = 0.05
    decay_penalty_weight = 0.1
    [decay]
    enabled = true
    archive_threshold = 0.1
    episodic_half_life_days = 30
    semantic_half_life_days = 365
    preference_half_life_days = 365
    instruction_half_life_days = 730
    [runtime]
    seed = 42
    database_path = "runtime/aira.db"
    offline = true
    debug = false
"""


def test_minimal_valid(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path, MINIMAL))
    assert cfg.generation.temperature == pytest.approx(0.8)
    # integer half-lives are coerced to float
    assert isinstance(cfg.decay.episodic_half_life_days, float)


def test_missing_section(tmp_path: Path) -> None:
    body = MINIMAL.replace("[runtime]\n    seed = 42\n", "")
    with pytest.raises(ConfigError, match=r"\[runtime\]"):
        load_config(_write(tmp_path, body))


def test_missing_key(tmp_path: Path) -> None:
    body = MINIMAL.replace("    top_k = 40\n", "")
    with pytest.raises(ConfigError, match="top_k"):
        load_config(_write(tmp_path, body))


def test_bad_backend(tmp_path: Path) -> None:
    body = MINIMAL.replace('backend = "auto"', 'backend = "elastic"')
    with pytest.raises(ConfigError, match="backend"):
        load_config(_write(tmp_path, body))


def test_weight_out_of_range(tmp_path: Path) -> None:
    body = MINIMAL.replace("lexical_weight = 0.4", "lexical_weight = 1.5")
    with pytest.raises(ConfigError, match="lexical_weight"):
        load_config(_write(tmp_path, body))


def test_heads_must_divide_dim(tmp_path: Path) -> None:
    body = MINIMAL.replace("heads = 8", "heads = 7")
    with pytest.raises(ConfigError, match="divisible"):
        load_config(_write(tmp_path, body))


def test_dropout_range(tmp_path: Path) -> None:
    body = MINIMAL.replace("dropout = 0.1", "dropout = 1.0")
    with pytest.raises(ConfigError, match="dropout"):
        load_config(_write(tmp_path, body))


def test_negative_seed(tmp_path: Path) -> None:
    body = MINIMAL.replace("seed = 42", "seed = -1")
    with pytest.raises(ConfigError, match="seed"):
        load_config(_write(tmp_path, body))


def test_bool_not_accepted_as_int(tmp_path: Path) -> None:
    body = MINIMAL.replace("layers = 8", "layers = true")
    with pytest.raises(ConfigError, match="layers"):
        load_config(_write(tmp_path, body))


def test_empty_owner(tmp_path: Path) -> None:
    body = MINIMAL.replace('default_owner_id = "local-user"', 'default_owner_id = "  "')
    with pytest.raises(ConfigError, match="default_owner_id"):
        load_config(_write(tmp_path, body))
