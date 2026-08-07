"""Errors for Aira Vault (persistence layer)."""

from __future__ import annotations


class VaultError(Exception):
    """Base class for persistence errors."""


class NotFoundError(VaultError):
    """A requested memory does not exist for the given owner."""


class ImportRejectedError(VaultError):
    """An import record failed validation, guard screening or schema checks."""
