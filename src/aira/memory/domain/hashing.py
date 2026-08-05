"""Content normalization, hashing and canonical keys.

Normalization and hashing are deterministic so duplicate detection, content hashes and
canonical keys are stable and reproducible across processes (invariant 12). No storage
is involved here.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from aira.memory.domain.enums import MemoryKind

_WHITESPACE = re.compile(r"\s+")


def normalize_content(text: str) -> str:
    """Return a normalized form of ``text`` with stable, deterministic output.

    Applies Unicode NFC normalization, strips leading/trailing whitespace and collapses
    internal runs of whitespace to a single space. Case is preserved.
    """
    normalized = unicodedata.normalize("NFC", text)
    return _WHITESPACE.sub(" ", normalized).strip()


def content_digest(text: str) -> str:
    """Return the SHA-256 hex digest of the normalized form of ``text``.

    Hashing the normalized form means trivially different inputs (extra spacing,
    Unicode form) produce the same digest.
    """
    normalized = normalize_content(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def canonical_key(kind: MemoryKind, content: str) -> str:
    """Derive a default canonical key for deduplication and superseding.

    The key is ``"<kind>:<casefolded normalized content>"``. It is a deterministic
    fallback: capture (Step 05) may supply a subject-based key so that a correction of
    the same fact shares a key with the original. Storage never depends on this format.
    """
    folded = normalize_content(content).casefold()
    return f"{kind.value}:{folded}"
