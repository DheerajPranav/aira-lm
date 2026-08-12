"""Versioned checkpoint save / load / resume for Aira Core.

A checkpoint bundles the model weights, optional optimizer state, the step count and the
model configuration, tagged with a schema version so incompatible checkpoints are
rejected rather than silently mis-loaded. Checkpoints are local files the user creates;
loading uses ``weights_only=False`` because the payload includes plain config dicts.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from aira.config import ModelConfig
from aira.core.model import AiraCore

CHECKPOINT_SCHEMA_VERSION = 1


def save_checkpoint(
    path: str | Path,
    *,
    model: AiraCore,
    model_config: ModelConfig,
    step: int,
    optimizer: torch.optim.Optimizer | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write a checkpoint to ``path`` and return it."""
    payload: dict[str, Any] = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict() if optimizer is not None else None,
        "step": step,
        "model_config": asdict(model_config),
        "extra": extra or {},
    }
    destination = Path(path)
    torch.save(payload, destination)
    return destination


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    """Load and version-check a checkpoint payload.

    Raises:
        ValueError: If the checkpoint schema version is unsupported.
    """
    payload: dict[str, Any] = torch.load(Path(path), map_location="cpu", weights_only=False)
    version = payload.get("schema_version")
    if version != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError(f"unsupported checkpoint schema_version: {version}")
    return payload


def resume(
    path: str | Path,
    *,
    model: AiraCore,
    optimizer: torch.optim.Optimizer | None = None,
) -> int:
    """Load weights (and optimizer state, if present) into place. Returns the saved step."""
    payload = load_checkpoint(path)
    model.load_state_dict(payload["model_state"])
    if optimizer is not None and payload.get("optimizer_state") is not None:
        optimizer.load_state_dict(payload["optimizer_state"])
    return int(payload["step"])
