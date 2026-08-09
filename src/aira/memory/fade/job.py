"""Aira Fade — the manually-invokable decay, archival and expiry job.

Deterministic given a fixed clock. It archives memories whose decay score falls below the
configured threshold and expires memories according to their retention policy. It **never
hard-deletes** — destructive deletion is always an explicit user action (governance).
Every transition it makes is audited by the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from aira.config import DecayConfig
from aira.memory.domain.enums import MemoryStatus, RetentionPolicy
from aira.memory.domain.records import MemoryRecord
from aira.memory.fade.decay import decay_score
from aira.memory.vault.repository import MemoryRepository


@dataclass(slots=True)
class FadeReport:
    """Counts and affected ids from one fade run."""

    scanned: int = 0
    archived: list[str] = field(default_factory=list)
    expired: list[str] = field(default_factory=list)

    @property
    def archived_count(self) -> int:
        """Number of memories archived in this run."""
        return len(self.archived)

    @property
    def expired_count(self) -> int:
        """Number of memories expired in this run."""
        return len(self.expired)


class FadeJob:
    """Applies decay-based archival and retention-based expiry on demand."""

    def __init__(self, repository: MemoryRepository, config: DecayConfig) -> None:
        """Create the job over a repository and the ``[decay]`` configuration."""
        self._repo = repository
        self._cfg = config

    def run(self, *, now: datetime, owner_id: str | None = None) -> FadeReport:
        """Run one fade pass. If ``owner_id`` is given, restrict to that owner.

        Expiry is checked before archival. Never hard-deletes.
        """
        report = FadeReport()
        if not self._cfg.enabled:
            return report

        owners = [owner_id] if owner_id is not None else self._repo.list_owners()
        for owner in owners:
            for record in self._repo.list_memories(
                owner, statuses=(MemoryStatus.ACTIVE,), limit=1_000_000
            ):
                report.scanned += 1
                if self._should_expire(record, now):
                    self._repo.expire(
                        owner, record.id, now=now, reason="expired by retention policy"
                    )
                    report.expired.append(record.id)
                elif self._should_archive(record, now):
                    self._repo.archive(
                        owner, record.id, now=now, reason="archived below decay threshold"
                    )
                    report.archived.append(record.id)
        return report

    def _should_expire(self, record: MemoryRecord, now: datetime) -> bool:
        if record.retention is RetentionPolicy.SESSION_ONLY:
            return True
        if record.retention is RetentionPolicy.FIXED_EXPIRY and record.expires_at is not None:
            return now >= record.expires_at
        return False

    def _should_archive(self, record: MemoryRecord, now: datetime) -> bool:
        return decay_score(record, now, self._cfg) < self._cfg.archive_threshold
