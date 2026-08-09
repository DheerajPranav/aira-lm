"""Aira Fade — decay, expiry and archival, off the request path.

A manually-invokable job that ages memories deterministically: archives stale ones and
expires them by retention policy. It never hard-deletes; destructive deletion is an
explicit user action handled by governance.
"""

from __future__ import annotations

from aira.memory.fade.decay import decay_score, half_life_days
from aira.memory.fade.job import FadeJob, FadeReport

__all__ = ["FadeJob", "FadeReport", "decay_score", "half_life_days"]
