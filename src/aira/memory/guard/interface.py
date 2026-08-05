"""Public types and protocol for Aira Guard.

Aira Guard is the pre-persistence safety and privacy gate. It inspects raw text and
decides whether it may be stored, redacts detected secrets, and produces a structured
result and an audit-safe event. **No output here ever carries a raw matched secret** —
findings hold only a category, a span offset and a redaction token.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from aira.memory.domain.enums import Sensitivity


class GuardDecision(StrEnum):
    """Whether content may be persisted."""

    ALLOW = "allow"
    BLOCK = "block"


class GuardCategory(StrEnum):
    """A category of restricted (secret) content that must not be persisted."""

    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    PRIVATE_KEY = "private_key"
    PASSWORD = "password"
    CREDENTIAL_URL = "credential_url"
    COOKIE = "cookie"
    PAYMENT_CARD = "payment_card"


# Human-safe replacement tokens. Never contain any part of a matched value.
REDACTION_TOKENS: dict[GuardCategory, str] = {
    GuardCategory.API_KEY: "[REDACTED:api_key]",
    GuardCategory.BEARER_TOKEN: "[REDACTED:bearer_token]",
    GuardCategory.PRIVATE_KEY: "[REDACTED:private_key]",
    GuardCategory.PASSWORD: "[REDACTED:password]",
    GuardCategory.CREDENTIAL_URL: "[REDACTED:credential_url]",
    GuardCategory.COOKIE: "[REDACTED:cookie]",
    GuardCategory.PAYMENT_CARD: "[REDACTED:payment_card]",
}


@dataclass(frozen=True, slots=True)
class GuardFinding:
    """One detected secret, described without exposing the matched value.

    ``start`` and ``length`` locate the match in the original text (for redaction); the
    raw substring is never stored on the finding.
    """

    category: GuardCategory
    start: int
    length: int
    confidence: float
    token: str


@dataclass(frozen=True, slots=True)
class GuardResult:
    """The outcome of scanning one piece of text.

    ``redacted_preview`` is safe to display and log: every detected secret has been
    replaced by a token. ``confidence`` is the guard's confidence in ``decision``.
    """

    decision: GuardDecision
    categories: tuple[GuardCategory, ...]
    reason: str
    confidence: float
    redacted_preview: str
    findings: tuple[GuardFinding, ...]
    sensitivity: Sensitivity
    do_not_remember: bool
    instruction_like: bool
    oversized: bool
    byte_length: int

    @property
    def blocked(self) -> bool:
        """Whether the content must not be persisted."""
        return self.decision is GuardDecision.BLOCK


@dataclass(frozen=True, slots=True)
class GuardEvent:
    """An audit-safe record of a guard decision.

    Carries only non-sensitive metadata and the already-redacted preview. It never
    contains the raw content or a hash of a blocked secret (invariant 7).
    """

    decision: GuardDecision
    categories: tuple[GuardCategory, ...]
    reason: str
    confidence: float
    sensitivity: Sensitivity
    do_not_remember: bool
    instruction_like: bool
    oversized: bool
    byte_length: int
    finding_count: int
    redacted_preview: str
    at: datetime
    owner_id: str | None = field(default=None)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe mapping. Contains no raw sensitive content."""
        return {
            "decision": self.decision.value,
            "categories": [c.value for c in self.categories],
            "reason": self.reason,
            "confidence": round(self.confidence, 4),
            "sensitivity": self.sensitivity.value,
            "do_not_remember": self.do_not_remember,
            "instruction_like": self.instruction_like,
            "oversized": self.oversized,
            "byte_length": self.byte_length,
            "finding_count": self.finding_count,
            "redacted_preview": self.redacted_preview,
            "at": self.at.isoformat(),
            "owner_id": self.owner_id,
        }


@runtime_checkable
class Guard(Protocol):
    """A replaceable pre-persistence safety and privacy gate."""

    def scan(
        self,
        content: str,
        *,
        owner_id: str | None = None,
        now: datetime | None = None,
    ) -> GuardResult:
        """Inspect ``content`` and return a :class:`GuardResult`."""
        ...
