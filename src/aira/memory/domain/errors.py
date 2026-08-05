"""Domain error types for Aira Memory.

Kept separate so persistence, policy and model layers can catch domain failures
without importing implementation modules.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all Aira Memory domain errors."""


class ValidationError(DomainError, ValueError):
    """A domain record or value failed validation."""


class IllegalTransitionError(DomainError):
    """A lifecycle transition was attempted from a status that does not allow it."""
