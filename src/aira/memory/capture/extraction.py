"""Deterministic candidate extraction from a raw turn.

Transparent, regex-based heuristics — no LLM, no embeddings. Patterns favour clear,
high-signal forms (explicit remember/forget, ``my <attr> is <value>``, ``I prefer
<value>``, identity, project, instruction). Structured attribute facts get a
subject-based canonical key so a later restatement or correction of the same attribute
supersedes the original; free-text and value-based preferences get content-based keys.

Explicit requests ("remember that …") carry stronger evidence than bare inferred
statements; corrections are marked so the evaluator can weight them.
"""

from __future__ import annotations

import re

from aira.memory.capture.models import Candidate, CandidateAction
from aira.memory.domain.enums import MemoryKind, MemoryLifetime, ProvenanceSource
from aira.memory.domain.hashing import normalize_content

# Attributes that read as preferences rather than plain facts.
_PREFERENCE_ATTRS = frozenset(
    {"editor", "theme", "shell", "language", "ide", "browser", "font", "os", "terminal"}
)

_CORRECTION_PREFIX = re.compile(
    r"^(?:actually|correction|update|wait|no|scratch that)\b[\s,:.-]*", re.IGNORECASE
)
_REMEMBER = re.compile(
    r"^(?:please\s+)?(?:remember|note|keep in mind)\s+(?:that\s+|to\s+)?(?P<rest>.+)$",
    re.IGNORECASE,
)
_FORGET = re.compile(
    r"^(?:please\s+)?(?:forget|delete|remove)\s+(?:about\s+)?(?P<target>.+)$",
    re.IGNORECASE,
)
_INSTRUCTION = re.compile(r"^(?:please\s+)?(?:always|from now on,?)\s+(?P<rest>.+)$", re.IGNORECASE)
_PROJECT = re.compile(
    r"^(?:i'?m|i am)\s+working\s+on\s+(?:the\s+)?(?:project\s+)?(?P<proj>.+)$"
    r"|^my\s+project\s+is\s+(?P<proj2>.+)$",
    re.IGNORECASE,
)
_NAME = re.compile(r"^(?:my\s+name\s+is|call\s+me)\s+(?P<name>.+)$", re.IGNORECASE)
_ATTR_FACT = re.compile(
    r"^my\s+(?P<attr>[a-z][a-z ]{0,30}?)\s+(?:is|are|=)\s+(?P<value>.+)$", re.IGNORECASE
)
_PREFERENCE = re.compile(r"^i\s+(?:prefer|like|love|favou?r|use)\s+(?P<value>.+)$", re.IGNORECASE)


def has_correction_marker(text: str) -> bool:
    """Return whether the turn opens with a correction cue (actually/no/update …)."""
    return _CORRECTION_PREFIX.match(text.strip()) is not None


def _key(kind: MemoryKind, owner_id: str, slot: str) -> str:
    return f"{kind.value}:{owner_id}:{normalize_content(slot).casefold()}"


def _excerpt(text: str) -> str:
    return normalize_content(text)[:120]


def extract_candidates(owner_id: str, text: str) -> list[Candidate]:
    """Extract zero or more candidates from a single turn."""
    body = text.strip()
    is_correction = has_correction_marker(body)
    if is_correction:
        body = _CORRECTION_PREFIX.sub("", body, count=1).strip()
        if not body:
            return []

    forget = _FORGET.match(body)
    if forget:
        return [_forget_candidate(owner_id, forget.group("target"))]

    remember = _REMEMBER.match(body)
    if remember:
        parsed = _parse_statement(
            owner_id,
            remember.group("rest"),
            source=ProvenanceSource.USER_EXPLICIT,
            method="explicit remember request",
            base_confidence=0.9,
            base_importance=0.7,
            allow_generic=True,
            is_correction=is_correction,
        )
        return [parsed] if parsed else []

    if is_correction:
        parsed = _parse_statement(
            owner_id,
            body,
            source=ProvenanceSource.USER_CORRECTION,
            method="user correction",
            base_confidence=0.85,
            base_importance=0.75,
            allow_generic=False,
            is_correction=True,
        )
        return [parsed] if parsed else []

    parsed = _parse_statement(
        owner_id,
        body,
        source=ProvenanceSource.USER_INFERRED,
        method="stated in conversation",
        base_confidence=0.6,
        base_importance=0.55,
        allow_generic=False,
        is_correction=False,
    )
    return [parsed] if parsed else []


def _forget_candidate(owner_id: str, target: str) -> Candidate:
    target = target.strip()
    attr = _ATTR_FROM_TARGET.match(target)
    if attr:
        slot = attr.group("attr")
        kind = _kind_for_attr(slot)
        key = _key(kind, owner_id, slot)
    else:
        kind = MemoryKind.SEMANTIC
        key = _key(kind, owner_id, target)
    return Candidate(
        action=CandidateAction.FORGET,
        kind=kind,
        canonical_key=key,
        content=normalize_content(target),
        source=ProvenanceSource.USER_EXPLICIT,
        method="explicit forget request",
        base_importance=0.5,
        base_confidence=0.9,
        source_excerpt=_excerpt(target),
    )


_ATTR_FROM_TARGET = re.compile(r"^(?:my\s+)?(?P<attr>[a-z][a-z ]{0,30})$", re.IGNORECASE)


def _kind_for_attr(attr: str) -> MemoryKind:
    return (
        MemoryKind.PREFERENCE
        if attr.strip().casefold() in _PREFERENCE_ATTRS
        else MemoryKind.SEMANTIC
    )


def _parse_statement(
    owner_id: str,
    statement: str,
    *,
    source: ProvenanceSource,
    method: str,
    base_confidence: float,
    base_importance: float,
    allow_generic: bool,
    is_correction: bool,
) -> Candidate | None:
    s = statement.strip().rstrip(".")
    if not s:
        return None

    instruction = _INSTRUCTION.match(s)
    if instruction:
        rest = instruction.group("rest")
        return _mk(
            CandidateAction.REMEMBER,
            MemoryKind.INSTRUCTION,
            _key(MemoryKind.INSTRUCTION, owner_id, rest),
            f"always {normalize_content(rest)}",
            source,
            method,
            max(base_importance, 0.8),
            base_confidence,
            is_correction,
        )

    project = _PROJECT.match(s)
    if project:
        proj = project.group("proj") or project.group("proj2") or ""
        return _mk(
            CandidateAction.REMEMBER,
            MemoryKind.SEMANTIC,
            _key(MemoryKind.SEMANTIC, owner_id, "project"),
            normalize_content(s),
            source,
            method,
            base_importance,
            base_confidence,
            is_correction,
            project=normalize_content(proj),
        )

    name = _NAME.match(s)
    if name:
        return _mk(
            CandidateAction.REMEMBER,
            MemoryKind.SEMANTIC,
            _key(MemoryKind.SEMANTIC, owner_id, "name"),
            normalize_content(s),
            source,
            method,
            base_importance,
            base_confidence,
            is_correction,
        )

    attr = _ATTR_FACT.match(s)
    if attr:
        slot = attr.group("attr").strip()
        kind = _kind_for_attr(slot)
        return _mk(
            CandidateAction.REMEMBER,
            kind,
            _key(kind, owner_id, slot),
            normalize_content(s),
            source,
            method,
            base_importance,
            base_confidence,
            is_correction,
        )

    preference = _PREFERENCE.match(s)
    if preference:
        value = preference.group("value")
        return _mk(
            CandidateAction.REMEMBER,
            MemoryKind.PREFERENCE,
            _key(MemoryKind.PREFERENCE, owner_id, value),
            normalize_content(s),
            source,
            method,
            base_importance,
            base_confidence,
            is_correction,
        )

    if allow_generic:
        return _mk(
            CandidateAction.REMEMBER,
            MemoryKind.SEMANTIC,
            _key(MemoryKind.SEMANTIC, owner_id, s),
            normalize_content(s),
            source,
            method,
            base_importance,
            base_confidence,
            is_correction,
        )
    return None


def _mk(
    action: CandidateAction,
    kind: MemoryKind,
    key: str,
    content: str,
    source: ProvenanceSource,
    method: str,
    importance: float,
    confidence: float,
    is_correction: bool,
    *,
    project: str | None = None,
) -> Candidate:
    return Candidate(
        action=action,
        kind=kind,
        canonical_key=key,
        content=content,
        source=source,
        method=method,
        base_importance=importance,
        base_confidence=confidence,
        lifetime=MemoryLifetime.LONG_TERM,
        project=project,
        is_correction=is_correction,
        source_excerpt=_excerpt(content),
    )
