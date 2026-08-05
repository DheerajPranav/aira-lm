"""Redaction: replace detected secret spans with safe tokens.

Produces a preview in which every detected secret has been removed, so the preview can
be displayed, logged and stored in guard events without leaking a value.
"""

from __future__ import annotations

from aira.memory.guard.detectors import RawFinding
from aira.memory.guard.interface import REDACTION_TOKENS

_MAX_PREVIEW_CHARS = 240


def _merge(findings: list[RawFinding]) -> list[tuple[int, int, str]]:
    """Merge overlapping spans, keeping the token of the highest-confidence finding."""
    if not findings:
        return []
    ordered = sorted(findings, key=lambda f: (f.start, f.end))
    merged: list[tuple[int, int, RawFinding]] = []
    for finding in ordered:
        if merged and finding.start <= merged[-1][1]:
            start, end, best = merged[-1]
            new_end = max(end, finding.end)
            new_best = finding if finding.confidence > best.confidence else best
            merged[-1] = (start, new_end, new_best)
        else:
            merged.append((finding.start, finding.end, finding))
    return [(s, e, REDACTION_TOKENS[f.category]) for s, e, f in merged]


def redact(content: str, findings: list[RawFinding]) -> str:
    """Return a length-capped preview with every detected secret replaced by a token."""
    spans = _merge(findings)
    if not spans:
        return _cap(content)
    parts: list[str] = []
    cursor = 0
    for start, end, token in spans:
        parts.append(content[cursor:start])
        parts.append(token)
        cursor = end
    parts.append(content[cursor:])
    return _cap("".join(parts))


def _cap(text: str) -> str:
    if len(text) <= _MAX_PREVIEW_CHARS:
        return text
    return text[:_MAX_PREVIEW_CHARS] + "…"
