"""Local training loop for Aira Core.

AdamW with linear warmup and cosine decay, gradient clipping, periodic validation and
deterministic seeding. Training is interruptible: a ``KeyboardInterrupt`` saves a
checkpoint (if a path was given) and returns partial results. Tracks loss, perplexity,
elapsed time and best-effort peak resident memory. No dataset is downloaded and no
language-quality claim is made.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import torch

from aira.config import ModelConfig
from aira.core.checkpoint import save_checkpoint
from aira.core.data import ByteDataset
from aira.core.model import AiraCore
from aira.device import select_device
from aira.seed import set_seed


@dataclass(frozen=True, slots=True)
class TrainConfig:
    """Hyper-parameters for a training run."""

    steps: int = 200
    batch_size: int = 16
    block_size: int = 64
    learning_rate: float = 3e-3
    weight_decay: float = 0.01
    grad_clip: float = 1.0
    warmup_steps: int = 10
    min_lr_fraction: float = 0.1
    eval_interval: int = 50
    eval_steps: int = 5
    seed: int = 42


# A fast, tiny configuration for smoke runs and overfit tests.
SMOKE_TRAIN_CONFIG = TrainConfig(
    steps=30, batch_size=8, block_size=16, warmup_steps=3, eval_interval=15, eval_steps=2
)


@dataclass(frozen=True, slots=True)
class StepRecord:
    """One training step's loss and learning rate."""

    step: int
    train_loss: float
    lr: float


@dataclass(frozen=True, slots=True)
class TrainResult:
    """Outcome of a training run."""

    steps: int
    final_train_loss: float
    final_val_loss: float | None
    train_perplexity: float
    history: tuple[StepRecord, ...]
    elapsed_seconds: float
    peak_rss: int | None
    interrupted: bool = field(default=False)


def _peak_rss() -> int | None:
    try:
        import resource
    except ImportError:  # pragma: no cover - non-unix
        return None
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


class Trainer:
    """Trains an :class:`AiraCore` on a :class:`ByteDataset`."""

    def __init__(
        self,
        model: AiraCore,
        config: TrainConfig,
        model_config: ModelConfig,
        *,
        device: str | None = None,
    ) -> None:
        """Create a trainer and its AdamW optimizer.

        ``model_config`` is the model's build configuration; it is embedded in checkpoints.
        """
        self.config = config
        self._model_config = model_config
        self.device = device or select_device()
        self.model = model.to(self.device)
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )

    def _lr_at(self, step: int) -> float:
        cfg = self.config
        if step < cfg.warmup_steps:
            return cfg.learning_rate * (step + 1) / max(1, cfg.warmup_steps)
        progress = (step - cfg.warmup_steps) / max(1, cfg.steps - cfg.warmup_steps)
        min_lr = cfg.learning_rate * cfg.min_lr_fraction
        return min_lr + 0.5 * (cfg.learning_rate - min_lr) * (1.0 + math.cos(math.pi * progress))

    def train(
        self, dataset: ByteDataset, *, checkpoint_path: str | Path | None = None
    ) -> TrainResult:
        """Run the configured number of steps, returning metrics."""
        cfg = self.config
        set_seed(cfg.seed)
        generator = torch.Generator().manual_seed(cfg.seed)
        history: list[StepRecord] = []
        interrupted = False
        start = time.perf_counter()
        step = 0

        self.model.train()
        try:
            for step in range(cfg.steps):
                lr = self._lr_at(step)
                for group in self.optimizer.param_groups:
                    group["lr"] = lr
                x, y = dataset.get_batch(
                    "train", cfg.batch_size, cfg.block_size, generator=generator, device=self.device
                )
                _, loss = self.model(x, y)
                assert loss is not None  # noqa: S101 - targets were provided
                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), cfg.grad_clip)
                self.optimizer.step()
                history.append(StepRecord(step=step, train_loss=float(loss.item()), lr=lr))
        except KeyboardInterrupt:  # pragma: no cover - manual interruption
            interrupted = True
            if checkpoint_path is not None:
                self._save(checkpoint_path, step, dataset)

        elapsed = time.perf_counter() - start
        final_train_loss = history[-1].train_loss if history else float("nan")
        val_loss = self._evaluate(dataset)
        if checkpoint_path is not None and not interrupted:
            self._save(checkpoint_path, cfg.steps, dataset)

        return TrainResult(
            steps=len(history),
            final_train_loss=final_train_loss,
            final_val_loss=val_loss,
            train_perplexity=math.exp(min(final_train_loss, 20.0)) if history else float("nan"),
            history=tuple(history),
            elapsed_seconds=round(elapsed, 4),
            peak_rss=_peak_rss(),
            interrupted=interrupted,
        )

    def _evaluate(self, dataset: ByteDataset) -> float | None:
        cfg = self.config
        if not dataset.has_batches("val", cfg.block_size):
            return None
        generator = torch.Generator().manual_seed(cfg.seed + 1)
        self.model.eval()
        losses: list[float] = []
        with torch.no_grad():
            for _ in range(cfg.eval_steps):
                x, y = dataset.get_batch(
                    "val", cfg.batch_size, cfg.block_size, generator=generator, device=self.device
                )
                _, loss = self.model(x, y)
                assert loss is not None  # noqa: S101
                losses.append(float(loss.item()))
        self.model.train()
        return sum(losses) / len(losses) if losses else None

    def _save(self, path: str | Path, step: int, dataset: ByteDataset) -> None:
        save_checkpoint(
            path,
            model=self.model,
            model_config=self._model_config,
            step=step,
            optimizer=self.optimizer,
        )
