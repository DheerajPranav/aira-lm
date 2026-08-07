"""The capture (write-path) service.

Turns a raw turn into planned memory operations and, optionally, applies them. The order
is fixed: guard first, then assistant/do-not-remember policy, then extraction, utility
evaluation, and conflict resolution (a canonical-key collision becomes a supersede; an
identical restatement is a duplicate; otherwise a new memory). Every decision is recorded
in a policy trace.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime

from aira.memory.capture.evaluation import evaluate
from aira.memory.capture.extraction import extract_candidates, has_correction_marker
from aira.memory.capture.models import (
    Assessment,
    Candidate,
    CandidateAction,
    CaptureOperation,
    CaptureResult,
    ForgetOp,
    IgnoreOp,
    RememberOp,
    Speaker,
    SupersedeOp,
    TraceEntry,
)
from aira.memory.domain.clock import utc_now
from aira.memory.domain.enums import (
    ConsentCategory,
    MemoryKind,
    RetentionPolicy,
    Sensitivity,
)
from aira.memory.domain.records import MemoryRecord, Provenance, make_memory
from aira.memory.guard.interface import Guard, GuardResult
from aira.memory.vault.repository import MemoryRepository

_CORRECTIBLE_KINDS = frozenset({MemoryKind.PREFERENCE, MemoryKind.SEMANTIC, MemoryKind.INSTRUCTION})


def _default_id() -> str:
    return uuid.uuid4().hex


class CaptureService:
    """Runs the write path: guard, extract, evaluate, resolve, (optionally) persist."""

    def __init__(
        self,
        guard: Guard,
        repository: MemoryRepository,
        *,
        new_id: Callable[[], str] = _default_id,
    ) -> None:
        """Create a capture service over a guard and a repository."""
        self._guard = guard
        self._repo = repository
        self._new_id = new_id

    def capture(
        self,
        owner_id: str,
        speaker: Speaker,
        text: str,
        *,
        now: datetime | None = None,
        debug: bool = False,  # noqa: ARG002 - trace is always built; flag reserved for callers
    ) -> CaptureResult:
        """Plan the operations for one turn without persisting them."""
        stamp = now if now is not None else utc_now()
        trace: list[TraceEntry] = []
        guard_result = self._guard.scan(text, owner_id=owner_id, now=stamp)
        trace.append(
            TraceEntry(
                "guard",
                f"decision={guard_result.decision.value}, "
                f"sensitivity={guard_result.sensitivity.value}",
            )
        )

        if guard_result.blocked:
            return self._single(
                IgnoreOp(f"blocked by guard: {guard_result.reason}"),
                trace,
                guard_result,
                blocked=True,
            )
        if speaker is Speaker.ASSISTANT:
            trace.append(TraceEntry("policy", "assistant statement is not promoted to a user fact"))
            return self._single(
                IgnoreOp("assistant statements are not promoted to user facts"), trace, guard_result
            )
        if guard_result.do_not_remember:
            trace.append(TraceEntry("policy", "do-not-remember requested"))
            return self._single(IgnoreOp("do-not-remember requested by user"), trace, guard_result)

        candidates = extract_candidates(owner_id, text)
        if not candidates:
            reason = (
                "ambiguous correction: no clear fact to update"
                if has_correction_marker(text)
                else "no durable fact detected"
            )
            trace.append(TraceEntry("extract", reason))
            return self._single(IgnoreOp(reason), trace, guard_result)

        operations: list[CaptureOperation] = []
        for candidate in candidates:
            operations.append(self._resolve(owner_id, candidate, guard_result, stamp, trace))
        return CaptureResult(tuple(operations), tuple(trace), guard_result)

    def apply(self, owner_id: str, result: CaptureResult, *, now: datetime | None = None) -> None:
        """Persist the write operations of a capture result."""
        for op in result.operations:
            if isinstance(op, RememberOp):
                self._repo.create(op.record, reason=op.reason)
            elif isinstance(op, SupersedeOp):
                self._repo.supersede(owner_id, op.old_id, op.replacement, now=now, reason=op.reason)
            elif isinstance(op, ForgetOp):
                self._repo.forget(owner_id, op.memory_id, now=now, reason=op.reason)
            # IgnoreOp: nothing to persist

    def process(
        self,
        owner_id: str,
        speaker: Speaker,
        text: str,
        *,
        now: datetime | None = None,
        debug: bool = False,
    ) -> CaptureResult:
        """Capture and apply in one call, using a single timestamp for both."""
        stamp = now if now is not None else utc_now()
        result = self.capture(owner_id, speaker, text, now=stamp, debug=debug)
        self.apply(owner_id, result, now=stamp)
        return result

    # --- internals -----------------------------------------------------------------

    def _resolve(
        self,
        owner_id: str,
        candidate: Candidate,
        guard_result: GuardResult,
        stamp: datetime,
        trace: list[TraceEntry],
    ) -> CaptureOperation:
        trace.append(
            TraceEntry(
                "extract",
                f"{candidate.kind.value}/{candidate.action.value} key={candidate.canonical_key}",
            )
        )
        if candidate.kind is MemoryKind.INSTRUCTION and guard_result.instruction_like:
            trace.append(TraceEntry("policy", "instruction-like/override content not promoted"))
            return IgnoreOp(
                "instruction-override content is not promoted to an instruction",
                candidate.source_excerpt,
            )

        assessment = evaluate(candidate)
        trace.append(TraceEntry("evaluate", "; ".join(assessment.reasons)))
        if not assessment.keep:
            return IgnoreOp(assessment.reasons[-1], candidate.source_excerpt)

        if candidate.action is CandidateAction.FORGET:
            existing = self._repo.find_active_by_canonical_key(owner_id, candidate.canonical_key)
            if existing is None:
                trace.append(TraceEntry("resolve", "nothing active to forget"))
                return IgnoreOp("nothing active to forget", candidate.source_excerpt)
            trace.append(TraceEntry("resolve", f"forget {existing.id}"))
            return ForgetOp(existing.id, f"forget requested for key {candidate.canonical_key}")

        existing = self._repo.find_active_by_canonical_key(owner_id, candidate.canonical_key)
        record = self._build_record(owner_id, candidate, assessment, guard_result, stamp)
        if existing is None:
            trace.append(TraceEntry("resolve", "no existing key -> REMEMBER"))
            return RememberOp(record, f"new {candidate.kind.value} memory")
        if existing.content == record.content:
            trace.append(TraceEntry("resolve", "identical restatement -> IGNORE (duplicate)"))
            return IgnoreOp("duplicate of an existing memory", candidate.source_excerpt)
        trace.append(TraceEntry("resolve", f"key collision -> SUPERSEDE {existing.id}"))
        return SupersedeOp(
            existing.id, record, f"supersedes {existing.id} on key {candidate.canonical_key}"
        )

    def _build_record(
        self,
        owner_id: str,
        candidate: Candidate,
        assessment: Assessment,
        guard_result: GuardResult,
        stamp: datetime,
    ) -> MemoryRecord:
        provenance = Provenance(
            source=candidate.source,
            actor=owner_id,
            method=candidate.method,
            captured_at=stamp,
            source_excerpt=candidate.source_excerpt or None,
        )
        return make_memory(
            id=self._new_id(),
            owner_id=owner_id,
            kind=candidate.kind,
            content=candidate.content,
            provenance=provenance,
            importance=assessment.importance,
            confidence=assessment.confidence,
            lifetime=candidate.lifetime,
            sensitivity=guard_result.sensitivity,
            consent=_consent_for(candidate, guard_result.sensitivity),
            retention=_retention_for(candidate),
            canonical_key=candidate.canonical_key,
            project=candidate.project,
            now=stamp,
        )

    def _single(
        self,
        op: CaptureOperation,
        trace: list[TraceEntry],
        guard_result: GuardResult,
        *,
        blocked: bool = False,
    ) -> CaptureResult:
        return CaptureResult((op,), tuple(trace), guard_result, blocked=blocked)


def _consent_for(candidate: Candidate, sensitivity: Sensitivity) -> ConsentCategory:
    if candidate.kind is MemoryKind.INSTRUCTION:
        return ConsentCategory.PERSISTENT_INSTRUCTIONS
    if candidate.project is not None:
        return ConsentCategory.PROJECT_CONTINUITY
    if sensitivity is Sensitivity.SENSITIVE:
        return ConsentCategory.SENSITIVE_PERSONAL_CONTEXT
    return ConsentCategory.PERSONALIZATION


def _retention_for(candidate: Candidate) -> RetentionPolicy:
    if candidate.kind in _CORRECTIBLE_KINDS:
        return RetentionPolicy.DURABLE_UNTIL_CORRECTION
    return RetentionPolicy.DURABLE_UNTIL_DELETION
