"""Tests for Aira Core training, checkpointing and generation."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from aira.config import ModelConfig
from aira.core import (
    SMOKE_TRAIN_CONFIG,
    TINY_CORPUS,
    AiraCore,
    ByteDataset,
    TrainConfig,
    Trainer,
    build_model,
    generate,
    load_checkpoint,
    resume,
    save_checkpoint,
)

_SMALL = ModelConfig(
    vocab_size=256,
    context_length=32,
    embedding_dim=64,
    layers=2,
    heads=4,
    ffn_multiplier=4,
    dropout=0.0,
    tie_embeddings=True,
)


def _model(seed: int = 0) -> AiraCore:
    return build_model(_SMALL, seed=seed)


def _gen() -> torch.Generator:
    return torch.Generator().manual_seed(0)


# --- dataset -----------------------------------------------------------------------


def test_batch_shapes_and_shift() -> None:
    ds = ByteDataset(TINY_CORPUS)
    x, y = ds.get_batch("train", 4, 16, generator=_gen())
    assert x.shape == (4, 16)
    assert y.shape == (4, 16)
    # y is x shifted by one (next-byte targets)
    assert torch.equal(x[:, 1:], y[:, :-1])


def test_deterministic_batch() -> None:
    ds = ByteDataset(TINY_CORPUS)
    x1, y1 = ds.get_batch("train", 4, 16, generator=torch.Generator().manual_seed(3))
    x2, y2 = ds.get_batch("train", 4, 16, generator=torch.Generator().manual_seed(3))
    assert torch.equal(x1, x2)
    assert torch.equal(y1, y2)


def test_dataset_boundaries() -> None:
    ds = ByteDataset(TINY_CORPUS)
    with pytest.raises(ValueError, match="empty"):
        ByteDataset("")
    with pytest.raises(ValueError, match="too small"):
        ds.get_batch("train", 2, 10_000, generator=_gen())
    with pytest.raises(ValueError, match="unknown split"):
        ds.get_batch("bogus", 2, 16, generator=_gen())


# --- training ----------------------------------------------------------------------


def test_one_step_training() -> None:
    trainer = Trainer(
        _model(), TrainConfig(steps=1, block_size=16, batch_size=4), _SMALL, device="cpu"
    )
    result = trainer.train(ByteDataset(TINY_CORPUS))
    assert result.steps == 1
    assert result.history[0].train_loss > 0


def test_overfit_loss_decreases() -> None:
    cfg = TrainConfig(steps=60, batch_size=8, block_size=16, warmup_steps=5, seed=1)
    trainer = Trainer(_model(), cfg, _SMALL, device="cpu")
    result = trainer.train(ByteDataset(TINY_CORPUS))
    assert result.final_train_loss < result.history[0].train_loss
    assert result.train_perplexity > 0
    assert result.final_val_loss is not None


def test_smoke_training_completes_on_cpu() -> None:
    trainer = Trainer(_model(), SMOKE_TRAIN_CONFIG, _SMALL, device="cpu")
    result = trainer.train(ByteDataset(TINY_CORPUS))
    assert result.steps == SMOKE_TRAIN_CONFIG.steps
    assert result.final_train_loss == result.final_train_loss  # finite (not NaN)


# --- checkpoints -------------------------------------------------------------------


def test_checkpoint_round_trip(tmp_path: Path) -> None:
    model = _model(seed=5)
    path = save_checkpoint(tmp_path / "ck.pt", model=model, model_config=_SMALL, step=7)
    payload = load_checkpoint(path)
    assert payload["step"] == 7
    assert payload["model_config"]["embedding_dim"] == 64

    fresh = _model(seed=999)
    step = resume(path, model=fresh)
    assert step == 7
    assert torch.equal(model.token_embedding.weight, fresh.token_embedding.weight)


def test_resume_restores_optimizer(tmp_path: Path) -> None:
    trainer = Trainer(
        _model(), TrainConfig(steps=5, block_size=16, batch_size=4), _SMALL, device="cpu"
    )
    trainer.train(ByteDataset(TINY_CORPUS), checkpoint_path=tmp_path / "ck.pt")

    fresh = Trainer(_model(seed=42), TrainConfig(steps=5), _SMALL, device="cpu")
    step = resume(tmp_path / "ck.pt", model=fresh.model, optimizer=fresh.optimizer)
    assert step == 5


def test_unsupported_checkpoint_schema_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pt"
    torch.save({"schema_version": 99}, bad)
    with pytest.raises(ValueError, match="schema_version"):
        load_checkpoint(bad)


# --- generation --------------------------------------------------------------------


def test_greedy_generation_is_deterministic() -> None:
    model = _model(seed=3)
    out1 = generate(model, "the ", max_new_tokens=16, temperature=0.0, device="cpu")
    out2 = generate(model, "the ", max_new_tokens=16, temperature=0.0, device="cpu")
    assert isinstance(out1, str)
    assert out1 == out2


def test_seeded_sampling_is_reproducible() -> None:
    model = _model(seed=3)
    a = generate(
        model, "the ", max_new_tokens=16, temperature=0.8, top_k=20, seed=123, device="cpu"
    )
    b = generate(
        model, "the ", max_new_tokens=16, temperature=0.8, top_k=20, seed=123, device="cpu"
    )
    assert a == b
    assert isinstance(a, str)
