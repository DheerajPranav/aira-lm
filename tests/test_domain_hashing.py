"""Tests for deterministic normalization, hashing and canonical keys."""

from __future__ import annotations

from aira.memory.domain import MemoryKind, canonical_key, content_digest, normalize_content


def test_normalize_collapses_whitespace_and_strips() -> None:
    assert normalize_content("  hello   world \n") == "hello world"


def test_normalize_is_idempotent() -> None:
    once = normalize_content("a\t b   c")
    assert normalize_content(once) == once


def test_normalize_unicode_nfc() -> None:
    # "e" + combining acute accent should normalize to the composed "é".
    decomposed = "café"
    composed = "café"
    assert normalize_content(decomposed) == normalize_content(composed)


def test_digest_is_deterministic() -> None:
    assert content_digest("alex prefers dark mode") == content_digest("alex prefers dark mode")


def test_digest_ignores_trivial_formatting() -> None:
    assert content_digest("alex  prefers dark mode") == content_digest("alex prefers dark mode ")


def test_digest_differs_on_different_content() -> None:
    assert content_digest("dark mode") != content_digest("light mode")


def test_digest_is_sha256_hex() -> None:
    digest = content_digest("x")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_canonical_key_deterministic_and_case_insensitive() -> None:
    a = canonical_key(MemoryKind.PREFERENCE, "Dark Mode")
    b = canonical_key(MemoryKind.PREFERENCE, "dark mode")
    assert a == b == "preference:dark mode"


def test_canonical_key_varies_by_kind() -> None:
    pref = canonical_key(MemoryKind.PREFERENCE, "dark mode")
    sem = canonical_key(MemoryKind.SEMANTIC, "dark mode")
    assert pref != sem
