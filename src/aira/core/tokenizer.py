"""Reversible UTF-8 byte tokenizer (vocabulary 256).

Every token is one byte, so the vocabulary is exactly 256 and any text round-trips
exactly through encode → decode. Decoding an arbitrary id sequence never raises: invalid
UTF-8 is replaced. This tokenizer has no learned parameters and needs no training.
"""

from __future__ import annotations

from collections.abc import Iterable

VOCAB_SIZE = 256


class ByteTokenizer:
    """Maps text to and from UTF-8 byte tokens (ids 0–255)."""

    vocab_size: int = VOCAB_SIZE

    def encode(self, text: str) -> list[int]:
        """Return the UTF-8 byte ids for ``text`` (always valid; lossless)."""
        return list(text.encode("utf-8"))

    def decode(self, ids: Iterable[int]) -> str:
        """Return text for a sequence of byte ids; invalid UTF-8 is replaced, never raised.

        Raises:
            ValueError: If any id is outside the 0–255 byte range.
        """
        as_list = list(ids)
        for token in as_list:
            if not 0 <= token < VOCAB_SIZE:
                raise ValueError(f"token id out of byte range [0, 255]: {token}")
        return bytes(as_list).decode("utf-8", errors="replace")

    def count(self, text: str) -> int:
        """Return the number of byte tokens in ``text`` (satisfies the budget Tokenizer)."""
        return len(text.encode("utf-8"))
