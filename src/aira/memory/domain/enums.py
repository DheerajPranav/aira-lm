"""Enumerations for the Aira Memory domain.

These closed vocabularies define how a memory is classified and where it sits in its
lifecycle. They are storage-independent: no SQL, no persistence, no model code.
"""

from __future__ import annotations

from enum import StrEnum


class MemoryAction(StrEnum):
    """Explicit, user-facing memory intents (see REQUIREMENTS).

    Distinct from lifecycle transitions (see :mod:`aira.memory.domain.lifecycle`):
    an action is what a user asks for; a transition is the resulting state change.
    """

    REMEMBER = "remember"
    UPDATE = "update"
    IGNORE = "ignore"
    RECALL = "recall"
    FORGET = "forget"


class MemoryKind(StrEnum):
    """What kind of thing a memory is. Independent of :class:`MemoryLifetime`."""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PREFERENCE = "preference"
    INSTRUCTION = "instruction"


class MemoryLifetime(StrEnum):
    """How long a memory is meant to live. Independent of :class:`MemoryKind`.

    ``WORKING`` is live context and is not persistent by default; ``KNOWLEDGE`` is
    external reference material kept logically separate from personal memory.
    """

    WORKING = "working"
    SESSION = "session"
    LONG_TERM = "long_term"
    KNOWLEDGE = "knowledge"


class MemoryStatus(StrEnum):
    """Lifecycle state of a persisted memory.

    ``DELETED`` is represented by a separate tombstone type that carries no content;
    a :class:`~aira.memory.domain.records.MemoryRecord` never holds this status.
    """

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    FORGOTTEN = "forgotten"
    DELETED = "deleted"


class Sensitivity(StrEnum):
    """Data-classification band (see DATA_CLASSIFICATION).

    ``RESTRICTED`` must never be stored by the initial system and is blocked before a
    record is ever constructed (Aira Guard, Step 03).
    """

    PUBLIC = "public"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


class ConsentCategory(StrEnum):
    """The consent basis under which a memory is retained."""

    PERSONALIZATION = "personalization"
    PROJECT_CONTINUITY = "project_continuity"
    PERSISTENT_INSTRUCTIONS = "persistent_instructions"
    SENSITIVE_PERSONAL_CONTEXT = "sensitive_personal_context"
    KNOWLEDGE_DOCUMENTS = "knowledge_documents"


class RetentionPolicy(StrEnum):
    """How long a memory is retained. ``PROHIBITED`` memories must not be persisted."""

    SESSION_ONLY = "session_only"
    FIXED_EXPIRY = "fixed_expiry"
    DURABLE_UNTIL_CORRECTION = "durable_until_correction"
    DURABLE_UNTIL_DELETION = "durable_until_deletion"
    PROHIBITED = "prohibited"


class ProvenanceSource(StrEnum):
    """How the system learned a memory (supports invariants 4 and 6).

    ``ASSISTANT`` marks assistant-generated statements, which are not promoted to user
    facts by default.
    """

    USER_EXPLICIT = "user_explicit"
    USER_CORRECTION = "user_correction"
    USER_INFERRED = "user_inferred"
    IMPORTED = "imported"
    ASSISTANT = "assistant"


# Only ACTIVE memories are eligible for normal retrieval and model context. Every other
# status is filtered out before ranking (invariant 2). Retrieval logic lives in Step 06,
# but the classification is defined here so the whole system shares one definition.
RETRIEVABLE_STATUSES: frozenset[MemoryStatus] = frozenset({MemoryStatus.ACTIVE})


def is_retrievable(status: MemoryStatus) -> bool:
    """Return whether a memory in this status may appear in normal retrieval."""
    return status in RETRIEVABLE_STATUSES
