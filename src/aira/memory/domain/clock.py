"""UTC time helpers for the memory domain.

The project uses UTC internally. These helpers produce and validate timezone-aware
UTC datetimes so timestamps are comparable and never naive.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aira.memory.domain.errors import ValidationError


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def ensure_utc(value: datetime, field: str) -> datetime:
    """Validate that ``value`` is a timezone-aware UTC datetime.

    Args:
        value: The datetime to check.
        field: Name of the field, used in the error message.

    Returns:
        The same datetime, normalized to the UTC timezone object.

    Raises:
        ValidationError: If the datetime is naive or not in UTC.
    """
    if value.tzinfo is None:
        raise ValidationError(f"{field} must be timezone-aware (UTC), got naive datetime")
    if value.utcoffset() != UTC.utcoffset(None):
        raise ValidationError(f"{field} must be in UTC, got offset {value.utcoffset()}")
    return value.astimezone(UTC)
