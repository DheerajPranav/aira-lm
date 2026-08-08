"""Minimal tokenizer interface for context-budget counting.

Aira enforces its context budget in *byte tokens*. The full reversible byte tokenizer is
Aira Core (Step 11); this module provides only what ranking needs — a `Tokenizer`
protocol and a `ByteTokenizer` that counts UTF-8 bytes — so budgeting is exact for
multibyte text without pulling in PyTorch.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Tokenizer(Protocol):
    """Counts tokens for budgeting. Aira Core's tokenizer will satisfy this too."""

    def count(self, text: str) -> int:
        """Return the number of tokens in ``text``."""
        ...


class ByteTokenizer:
    """Counts tokens as UTF-8 bytes (vocabulary 256). Exact for any Unicode text."""

    def count(self, text: str) -> int:
        """Return the UTF-8 byte length of ``text``."""
        return len(text.encode("utf-8"))
