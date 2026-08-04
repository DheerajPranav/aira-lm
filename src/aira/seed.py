"""Deterministic seeding utilities.

Seeds the standard-library ``random`` module and, if they are importable, ``numpy``
and ``torch`` — best-effort, so the memory runtime stays free of a hard PyTorch
dependency. Determinism is a project requirement for reproducible tests and
benchmarks.
"""

from __future__ import annotations

import random


def set_seed(seed: int) -> int:
    """Seed all available random sources for reproducibility.

    Seeds the standard-library ``random`` generator always, and ``numpy`` / ``torch``
    if they are installed. Missing optional libraries are ignored so this works in the
    dependency-light memory runtime.

    Args:
        seed: A non-negative integer seed.

    Returns:
        The seed that was applied (echoed for convenience/logging).

    Raises:
        ValueError: If ``seed`` is negative.
    """
    if seed < 0:
        raise ValueError(f"seed must be >= 0, got {seed}")

    random.seed(seed)
    _seed_numpy(seed)
    _seed_torch(seed)
    return seed


def _seed_numpy(seed: int) -> None:
    try:
        import numpy as np
    except ImportError:
        return
    np.random.seed(seed)


def _seed_torch(seed: int) -> None:
    try:
        import torch
    except ImportError:
        return
    torch.manual_seed(seed)
