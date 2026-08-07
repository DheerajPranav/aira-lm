"""Aira capture — the deterministic write path.

Extracts candidates from a turn, screens them through Aira Guard, evaluates their
utility, resolves corrections against existing memories by superseding, and produces
planned operations with a policy trace. No LLM, no embeddings, no retrieval.
"""

from __future__ import annotations

from aira.memory.capture.evaluation import (
    CONFIDENCE_THRESHOLD,
    IMPORTANCE_THRESHOLD,
    evaluate,
)
from aira.memory.capture.extraction import extract_candidates
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
from aira.memory.capture.service import CaptureService

__all__ = [
    "CONFIDENCE_THRESHOLD",
    "IMPORTANCE_THRESHOLD",
    "Assessment",
    "Candidate",
    "CandidateAction",
    "CaptureOperation",
    "CaptureResult",
    "CaptureService",
    "ForgetOp",
    "IgnoreOp",
    "RememberOp",
    "Speaker",
    "SupersedeOp",
    "TraceEntry",
    "evaluate",
    "extract_candidates",
]
