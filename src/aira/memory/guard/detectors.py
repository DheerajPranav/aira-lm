"""Deterministic secret and policy detectors.

Each detector reports the *span* of a match (start/end offsets) and a category, never
the matched substring. The raw text stays inside this module only long enough to locate
spans; nothing derived from a secret value leaves via a detector.

The trade-off is precision over recall: patterns favour well-known, high-signal secret
forms and keyword-anchored assignments to keep false positives low. This is documented,
not exhaustive; see ``docs`` and the guard tests for the covered categories.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from aira.memory.guard.interface import GuardCategory


@dataclass(frozen=True, slots=True)
class RawFinding:
    """Internal-only span of a detected secret. Never leaves the guard as raw text."""

    category: GuardCategory
    start: int
    end: int
    confidence: float


# --- secret patterns ---------------------------------------------------------------
# Each entry: (category, compiled pattern, confidence).
_PATTERNS: list[tuple[GuardCategory, re.Pattern[str], float]] = [
    # Multiline PEM private-key blocks.
    (
        GuardCategory.PRIVATE_KEY,
        re.compile(
            r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----.*?"
            r"-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----",
            re.DOTALL,
        ),
        0.99,
    ),
    # Well-known API-key prefixes.
    (GuardCategory.API_KEY, re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0.97),
    (GuardCategory.API_KEY, re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), 0.96),
    (GuardCategory.API_KEY, re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), 0.95),
    (GuardCategory.API_KEY, re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), 0.95),
    (GuardCategory.API_KEY, re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"), 0.96),
    (GuardCategory.API_KEY, re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), 0.90),
    # Keyword-anchored generic API/secret assignment.
    (
        GuardCategory.API_KEY,
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?key|client[_-]?secret)\b"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?",
        ),
        0.85,
    ),
    # Bearer tokens and JWTs.
    (GuardCategory.BEARER_TOKEN, re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{10,}\b"), 0.85),
    (
        GuardCategory.BEARER_TOKEN,
        re.compile(r"\beyJ[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}\b"),
        0.90,
    ),
    # password = value / password: "value"
    (
        GuardCategory.PASSWORD,
        re.compile(
            r"(?i)\b(?:password|passwd|pwd)\b\s*[:=]\s*(?:\"[^\"]{4,}\"|'[^']{4,}'|\S{6,})",
        ),
        0.80,
    ),
    # scheme://user:password@host
    (
        GuardCategory.CREDENTIAL_URL,
        re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s:/@]+:[^\s:/@]+@[^\s/]+"),
        0.90,
    ),
    # Cookie headers and known auth-cookie names.
    (
        GuardCategory.COOKIE,
        re.compile(r"(?i)\b(?:set-cookie|cookie)\s*:\s*\S+=[A-Za-z0-9._\-]{6,}"),
        0.75,
    ),
    (
        GuardCategory.COOKIE,
        re.compile(
            r"(?i)\b(?:sessionid|session_id|sid|auth_token|access_token|refresh_token)\b"
            r"\s*[:=]\s*[A-Za-z0-9._\-]{8,}",
        ),
        0.72,
    ),
]

_CARD_CANDIDATE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def _luhn_ok(digits: str) -> bool:
    """Return whether ``digits`` (a run of decimal digits) passes the Luhn checksum."""
    total = 0
    parity = len(digits) % 2
    for i, ch in enumerate(digits):
        d = ord(ch) - 48
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _find_payment_cards(content: str) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for m in _CARD_CANDIDATE.finditer(content):
        digits = re.sub(r"[ -]", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            findings.append(RawFinding(GuardCategory.PAYMENT_CARD, m.start(), m.end(), 0.90))
    return findings


def find_secrets(content: str) -> list[RawFinding]:
    """Return all detected secret spans, sorted by start offset.

    Spans may overlap when multiple detectors match; the guard merges them for redaction.
    """
    findings: list[RawFinding] = []
    for category, pattern, confidence in _PATTERNS:
        for m in pattern.finditer(content):
            findings.append(RawFinding(category, m.start(), m.end(), confidence))
    findings.extend(_find_payment_cards(content))
    findings.sort(key=lambda f: (f.start, f.end))
    return findings


# --- policy detectors (not secrets) ------------------------------------------------

_DO_NOT_REMEMBER = re.compile(
    r"\b(?:do not|don'?t|please don'?t|no need to)\s+(?:remember|store|save|keep|record)\b"
    r"|\b(?:forget (?:this|that|it))\b"
    r"|\b(?:this is (?:just )?(?:temporary|off the record|between us))\b",
    re.IGNORECASE,
)

_POLICY_OVERRIDE = re.compile(
    r"\b(?:ignore|disregard|override|forget)\b[^.\n]{0,40}\b"
    r"(?:previous|prior|above|all|the|your|system|safety)?\b[^.\n]{0,20}\b"
    r"(?:instructions?|rules?|prompts?|policy|policies|guardrails?)\b"
    r"|\byou are now\b|\bnew (?:system )?(?:instructions?|rules?)\b",
    re.IGNORECASE,
)


def detect_do_not_remember(content: str) -> bool:
    """Return whether the text explicitly asks not to be remembered/stored."""
    return _DO_NOT_REMEMBER.search(content) is not None


def detect_policy_override(content: str) -> bool:
    """Return whether the text contains instruction/policy-override language.

    Such content is flagged as untrusted (it is treated as data, never promoted to
    system instructions) but is not itself a reason to block persistence.
    """
    return _POLICY_OVERRIDE.search(content) is not None
