"""Aira Core — the compact decoder-only transformer.

A reversible byte tokenizer (vocabulary 256) and a small GPT-style causal language model
implemented directly in PyTorch, plus a `TinyTransformerBackend` adapter to the chat
generation interface. Training, checkpoints and sampling generation arrive in Step 12;
this module has forward, causal loss, greedy decoding and an exact parameter count, and
makes no training or quality claim.

PyTorch is an optional dependency (the ``core`` extra); importing this package requires it.
"""

from __future__ import annotations

from aira.core.backend import TinyTransformerBackend
from aira.core.checkpoint import (
    CHECKPOINT_SCHEMA_VERSION,
    load_checkpoint,
    resume,
    save_checkpoint,
)
from aira.core.data import TINY_CORPUS, ByteDataset
from aira.core.generate import generate
from aira.core.model import (
    AiraCore,
    Block,
    CausalSelfAttention,
    FeedForward,
    build_model,
    from_config,
)
from aira.core.tokenizer import VOCAB_SIZE, ByteTokenizer
from aira.core.train import (
    SMOKE_TRAIN_CONFIG,
    StepRecord,
    TrainConfig,
    Trainer,
    TrainResult,
)

__all__ = [
    "CHECKPOINT_SCHEMA_VERSION",
    "SMOKE_TRAIN_CONFIG",
    "TINY_CORPUS",
    "VOCAB_SIZE",
    "AiraCore",
    "Block",
    "ByteDataset",
    "ByteTokenizer",
    "CausalSelfAttention",
    "FeedForward",
    "StepRecord",
    "TinyTransformerBackend",
    "TrainConfig",
    "TrainResult",
    "Trainer",
    "build_model",
    "from_config",
    "generate",
    "load_checkpoint",
    "resume",
    "save_checkpoint",
]
