"""Local byte-level dataset and fixed-length causal batching.

Text is tokenized to byte ids and split into train/validation. Batches are contiguous
windows: ``x = data[i:i+block]`` and ``y = data[i+1:i+block+1]`` (next-byte targets), so
``x[:, 1:] == y[:, :-1]``. Sampling is deterministic given a ``torch.Generator``. Nothing
is downloaded; the corpus is supplied by the caller or the tiny built-in sample.
"""

from __future__ import annotations

import torch
from torch import Tensor

from aira.core.tokenizer import ByteTokenizer

# A tiny, repetitive local sample corpus for smoke training and overfit tests. It is
# deliberately small and structured; it makes no claim of being training-grade data.
_PARAGRAPH = (
    "aira remembers what matters and forgets responsibly. "
    "the user prefers dark mode. the editor is vim. the project is falcon. "
    "small model, long memory, gentle by design. "
)
TINY_CORPUS = _PARAGRAPH * 40


class ByteDataset:
    """A byte-tokenized corpus split into train/validation with causal batching."""

    def __init__(
        self,
        text: str,
        *,
        val_fraction: float = 0.1,
        tokenizer: ByteTokenizer | None = None,
    ) -> None:
        """Tokenize ``text`` and split off a validation tail.

        Raises:
            ValueError: If ``val_fraction`` is not in [0, 1) or the corpus is empty.
        """
        if not 0.0 <= val_fraction < 1.0:
            raise ValueError("val_fraction must be in [0, 1)")
        tok = tokenizer or ByteTokenizer()
        ids = tok.encode(text)
        if not ids:
            raise ValueError("corpus is empty")
        data = torch.tensor(ids, dtype=torch.long)
        split = int(len(data) * (1.0 - val_fraction))
        self._train = data[:split]
        self._val = data[split:]

    def split_size(self, split: str) -> int:
        """Return the number of tokens in ``'train'`` or ``'val'``."""
        return int(self._data(split).numel())

    def has_batches(self, split: str, block_size: int) -> bool:
        """Whether a split can yield at least one window of ``block_size``."""
        return self._data(split).numel() - block_size - 1 >= 1

    def get_batch(
        self,
        split: str,
        batch_size: int,
        block_size: int,
        *,
        generator: torch.Generator | None = None,
        device: str | torch.device = "cpu",
    ) -> tuple[Tensor, Tensor]:
        """Return a deterministic ``(x, y)`` batch of next-byte prediction windows.

        Raises:
            ValueError: If the split is too small for ``block_size``.
        """
        data = self._data(split)
        max_start = data.numel() - block_size - 1
        if max_start < 1:
            raise ValueError(f"split '{split}' too small for block_size {block_size}")
        starts = torch.randint(0, max_start, (batch_size,), generator=generator)
        x = torch.stack([data[i : i + block_size] for i in starts])
        y = torch.stack([data[i + 1 : i + block_size + 1] for i in starts])
        return x.to(device), y.to(device)

    def _data(self, split: str) -> Tensor:
        if split == "train":
            return self._train
        if split == "val":
            return self._val
        raise ValueError(f"unknown split '{split}' (expected 'train' or 'val')")
