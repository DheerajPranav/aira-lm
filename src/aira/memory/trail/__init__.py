"""Aira Trail — provenance and append-only audit events.

Audit events record *that* a lifecycle change happened and why, without retaining
content. Hard-delete events in particular carry no content or content-derived metadata
(invariants 2 and 7).
"""

from __future__ import annotations

from aira.memory.trail.events import AuditAction, AuditEvent, new_event_id

__all__ = ["AuditAction", "AuditEvent", "new_event_id"]
