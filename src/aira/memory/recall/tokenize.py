"""Deterministic tokenization and safe query-term building for retrieval.

The same tokenizer feeds the BM25 fallback and the FTS5 query builder, so both backends
agree on what a "term" is. Query terms are also used to build a safe FTS5 MATCH
expression (each term quoted), which avoids FTS query-syntax errors on arbitrary input.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")

# Bounds to keep retrieval work predictable (denial-of-service controls).
MAX_QUERY_CHARS = 512
MAX_QUERY_TERMS = 32


def tokenize(text: str) -> list[str]:
    """Split text into lowercase alphanumeric tokens."""
    return _TOKEN.findall(text.lower())


def query_terms(query: str, *, max_chars: int = MAX_QUERY_CHARS) -> list[str]:
    """Return de-duplicated query terms (order preserved), bounded in size.

    An empty or whitespace-only query yields an empty list.
    """
    trimmed = query[:max_chars]
    seen: dict[str, None] = {}
    for token in tokenize(trimmed):
        seen.setdefault(token, None)
        if len(seen) >= MAX_QUERY_TERMS:
            break
    return list(seen)


def fts_match_expression(terms: list[str]) -> str:
    """Build a safe FTS5 MATCH expression from terms (each quoted, OR-combined)."""
    return " OR ".join(f'"{term}"' for term in terms)
