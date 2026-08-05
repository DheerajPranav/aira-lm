"""The default deterministic implementation of Aira Guard.

Orchestrates the detectors, redaction and a lightweight sensitivity classifier into a
single :class:`~aira.memory.guard.interface.GuardResult`, enforces an input-size limit,
and builds an audit-safe :class:`~aira.memory.guard.interface.GuardEvent`. It never
returns or logs a raw secret.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from aira.memory.domain.clock import ensure_utc, utc_now
from aira.memory.domain.enums import Sensitivity
from aira.memory.guard.detectors import (
    detect_do_not_remember,
    detect_policy_override,
    find_secrets,
)
from aira.memory.guard.interface import (
    REDACTION_TOKENS,
    GuardCategory,
    GuardDecision,
    GuardEvent,
    GuardFinding,
    GuardResult,
)
from aira.memory.guard.redaction import redact

_LOGGER = logging.getLogger("aira.memory.guard")

# Default maximum accepted input size, in bytes (mirrors configs/aira_tiny.toml).
DEFAULT_MAX_INPUT_BYTES = 8192

# Keyword hints for the SENSITIVE band. Deterministic and intentionally conservative;
# this is a classification hook, not an exhaustive PII classifier.
_SENSITIVE_HINTS = re.compile(
    r"(?i)\b(?:diagnos\w*|prescription|medication|blood pressure|hiv|cancer|depression|"
    r"anxiety|therapy|salary|bank account|iban|routing number|ssn|social security|"
    r"home address|lawsuit|arrest|indict\w*|divorce|immigration status)\b"
)


def _unique(categories: list[GuardCategory]) -> tuple[GuardCategory, ...]:
    seen: dict[GuardCategory, None] = {}
    for c in categories:
        seen.setdefault(c, None)
    return tuple(seen)


def classify_sensitivity(content: str, *, has_secret: bool) -> Sensitivity:
    """Classify content into a data-sensitivity band.

    Restricted always wins (a detected secret); otherwise a conservative keyword hint
    marks SENSITIVE, and the default for user content is PERSONAL.
    """
    if has_secret:
        return Sensitivity.RESTRICTED
    if _SENSITIVE_HINTS.search(content) is not None:
        return Sensitivity.SENSITIVE
    return Sensitivity.PERSONAL


class DeterministicGuard:
    """A deterministic, offline safety and privacy gate (the default :class:`Guard`)."""

    def __init__(self, *, max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES) -> None:
        """Create a guard.

        Args:
            max_input_bytes: Inputs larger than this (UTF-8 encoded) are blocked without
                being scanned, bounding work and memory (a denial-of-service control).
        """
        if max_input_bytes <= 0:
            raise ValueError("max_input_bytes must be > 0")
        self._max_input_bytes = max_input_bytes

    def scan(
        self,
        content: str,
        *,
        owner_id: str | None = None,
        now: datetime | None = None,
    ) -> GuardResult:
        """Inspect ``content`` and return a decision with a redacted preview.

        Oversized input is blocked and not scanned. Detected secrets block persistence;
        do-not-remember and instruction-like signals are reported but do not block.
        """
        byte_length = len(content.encode("utf-8"))
        if byte_length > self._max_input_bytes:
            limit = self._max_input_bytes
            return GuardResult(
                decision=GuardDecision.BLOCK,
                categories=(),
                reason=f"input exceeds maximum size ({byte_length} > {limit} bytes)",
                confidence=1.0,
                redacted_preview="<oversized input omitted>",
                findings=(),
                sensitivity=Sensitivity.PERSONAL,
                do_not_remember=False,
                instruction_like=False,
                oversized=True,
                byte_length=byte_length,
            )

        raw = find_secrets(content)
        findings = tuple(
            GuardFinding(
                category=r.category,
                start=r.start,
                length=r.end - r.start,
                confidence=r.confidence,
                token=REDACTION_TOKENS[r.category],
            )
            for r in raw
        )
        categories = _unique([r.category for r in raw])
        preview = redact(content, raw)
        do_not_remember = detect_do_not_remember(content)
        instruction_like = detect_policy_override(content)
        has_secret = bool(findings)
        sensitivity = classify_sensitivity(content, has_secret=has_secret)

        if has_secret:
            decision = GuardDecision.BLOCK
            confidence = max(f.confidence for f in findings)
            reason = "blocked restricted content: " + ", ".join(c.value for c in categories)
        else:
            decision = GuardDecision.ALLOW
            confidence = 1.0
            notes = ["no restricted content detected"]
            if instruction_like:
                notes.append("instruction-like content flagged as untrusted")
            if do_not_remember:
                notes.append("do-not-remember requested")
            reason = "; ".join(notes)

        result = GuardResult(
            decision=decision,
            categories=categories,
            reason=reason,
            confidence=confidence,
            redacted_preview=preview,
            findings=findings,
            sensitivity=sensitivity,
            do_not_remember=do_not_remember,
            instruction_like=instruction_like,
            oversized=False,
            byte_length=byte_length,
        )
        if result.blocked:
            # Log only safe metadata — never the raw content or a secret value.
            _LOGGER.warning(
                "aira.guard blocked content: categories=%s confidence=%.2f bytes=%d",
                [c.value for c in categories],
                confidence,
                byte_length,
            )
        return result

    def build_event(
        self,
        result: GuardResult,
        *,
        owner_id: str | None = None,
        now: datetime | None = None,
    ) -> GuardEvent:
        """Build an audit-safe event from a scan result. Contains no raw content."""
        at = ensure_utc(now, "now") if now is not None else utc_now()
        return GuardEvent(
            decision=result.decision,
            categories=result.categories,
            reason=result.reason,
            confidence=result.confidence,
            sensitivity=result.sensitivity,
            do_not_remember=result.do_not_remember,
            instruction_like=result.instruction_like,
            oversized=result.oversized,
            byte_length=result.byte_length,
            finding_count=len(result.findings),
            redacted_preview=result.redacted_preview,
            at=at,
            owner_id=owner_id,
        )


def default_guard(*, max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES) -> DeterministicGuard:
    """Return the default deterministic guard."""
    return DeterministicGuard(max_input_bytes=max_input_bytes)
