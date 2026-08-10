"""Executes benchmark scenarios against the memory runtime and collects outcomes.

Each scenario runs on a fresh in-memory engine with a fixed, monotonically increasing
clock, so results are deterministic. Retrieval metrics are computed under three baselines
(no-memory, Aira Memory, full-history); the four zero-tolerance checks come from the
forget / cross-owner / secret / budget scenarios.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from aira.chat import ChatEngine, create_chat_engine
from aira.config import AiraConfig
from aira.evaluation import metrics
from aira.evaluation.scenarios import Kind, Scenario, default_scenarios
from aira.memory.domain.enums import RetentionPolicy
from aira.memory.governance import ImportRejectedError
from aira.memory.ranking import OPEN_TAG
from aira.memory.recall.models import RetrievalFilters, RetrievalResult
from aira.memory.vault import connect

_BASE_TIME = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
_MALFORMED_IMPORT = '{"schema_version": 1, "content": "hi"}'


class _Clock:
    def __init__(self, base: datetime) -> None:
        self._t = base

    def tick(self) -> datetime:
        self._t += timedelta(minutes=1)
        return self._t


class _FailingRetriever:
    """A retriever that always fails, to exercise graceful degradation."""

    def search(
        self, owner_id: str, query: str, *, filters: RetrievalFilters | None = None, limit: int = 5
    ) -> list[RetrievalResult]:
        raise TimeoutError("injected retrieval failure")


@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    """The result of running one scenario."""

    id: str
    category: str
    kind: str
    passed: bool
    detail: str = ""
    precision: float | None = None
    recall: float | None = None
    recall_at_k: float | None = None
    mrr: float | None = None
    baselines: dict[str, dict[str, float]] | None = None
    leaked: bool | None = None
    secret_persisted: bool | None = None
    budget_violation: bool | None = None
    degraded_success: bool | None = None
    correction_success: bool | None = None
    latency_ms: float = 0.0
    context_tokens: int = 0

    def canonical(self) -> dict[str, Any]:
        """A latency-free, reproducible summary for report comparison."""
        return {
            "id": self.id,
            "kind": self.kind,
            "passed": self.passed,
            "precision": self.precision,
            "recall": self.recall,
            "mrr": self.mrr,
            "leaked": self.leaked,
            "secret_persisted": self.secret_persisted,
            "budget_violation": self.budget_violation,
            "degraded_success": self.degraded_success,
            "correction_success": self.correction_success,
        }


@dataclass(slots=True)
class BenchRunner:
    """Runs scenarios and returns their outcomes."""

    config: AiraConfig
    _top_k: int = field(init=False)

    def __post_init__(self) -> None:
        self._top_k = self.config.memory.top_k

    def run(self, scenarios: Sequence[Scenario] | None = None) -> list[ScenarioOutcome]:
        """Run all scenarios (defaults to the built-in set)."""
        cases = list(scenarios) if scenarios is not None else default_scenarios()
        return [self._run_one(case) for case in cases]

    # --- per-scenario execution ----------------------------------------------------

    def _run_one(self, scenario: Scenario) -> ScenarioOutcome:
        engine = create_chat_engine(self.config, connect(":memory:"))
        clock = _Clock(_BASE_TIME)
        for step in scenario.setup:
            engine.chat(step.owner, step.text, now=clock.tick())
        handler = _HANDLERS[scenario.kind]
        return handler(self, engine, scenario, clock)

    def _metric_set(self, retrieved: list[str], relevant: set[str]) -> dict[str, float]:
        return {
            "precision": metrics.precision(retrieved, relevant),
            "recall": metrics.recall(retrieved, relevant),
            "recall_at_k": metrics.recall_at_k(retrieved, relevant, self._top_k),
            "mrr": metrics.reciprocal_rank(retrieved, relevant),
        }

    def _recall_like(
        self, engine: ChatEngine, scenario: Scenario, clock: _Clock, *, is_correction: bool
    ) -> ScenarioOutcome:
        owner = scenario.query_owner
        start = time.perf_counter()
        included, block, _count = engine.retrieve(owner, scenario.query_text, now=clock.tick())
        latency = round((time.perf_counter() - start) * 1000, 3)

        active = engine.memories(owner)
        relevant_ids = {r.id for r in active if _contains_any(r.content, scenario.relevant)}
        retrieved_ids = [r.id for r in included]

        baselines = {
            "no_memory": self._metric_set([], relevant_ids),
            "aira": self._metric_set(retrieved_ids, relevant_ids),
            "full_history": self._metric_set([r.id for r in active], relevant_ids),
        }
        leaked = _contains_any(block.text, scenario.forbidden) if scenario.forbidden else None
        fact_stored = bool(relevant_ids) if scenario.relevant else True
        recalled = baselines["aira"]["recall"] >= 1.0 - 1e-9
        passed = fact_stored and recalled and leaked is not True
        detail = (
            ""
            if passed
            else ("expected fact not stored" if not fact_stored else "not recalled/leaked")
        )
        return ScenarioOutcome(
            id=scenario.id,
            category=scenario.category.value,
            kind=scenario.kind.value,
            passed=passed,
            detail=detail,
            precision=baselines["aira"]["precision"],
            recall=baselines["aira"]["recall"],
            recall_at_k=baselines["aira"]["recall_at_k"],
            mrr=baselines["aira"]["mrr"],
            baselines=baselines,
            leaked=leaked,
            correction_success=passed if is_correction else None,
            latency_ms=latency,
            context_tokens=block.token_count,
        )

    # --- handlers ------------------------------------------------------------------

    def _h_recall(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        return self._recall_like(engine, s, clock, is_correction=False)

    def _h_correction(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        return self._recall_like(engine, s, clock, is_correction=True)

    def _h_forget(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        included, block, _ = engine.retrieve(s.query_owner, s.query_text, now=clock.tick())
        leaked = _contains_any(block.text, s.forbidden)
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=not leaked,
            detail="forgotten memory leaked" if leaked else "",
            leaked=leaked,
            context_tokens=block.token_count,
        )

    def _h_cross_owner(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        _, block, _ = engine.retrieve(s.query_owner, s.query_text, now=clock.tick())
        leaked = _contains_any(block.text, s.forbidden)
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=not leaked,
            detail="cross-owner leak" if leaked else "",
            leaked=leaked,
            context_tokens=block.token_count,
        )

    def _h_secret(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        owner = s.setup[0].owner if s.setup else s.query_owner
        stored = engine.governance.inspect_all(owner, include_inactive=True)
        persisted = any(s.secret in r.content for r in stored)
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=not persisted,
            detail="secret persisted" if persisted else "",
            secret_persisted=persisted,
        )

    def _h_budget(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        _, block, _ = engine.retrieve(s.query_owner, s.query_text, now=clock.tick())
        violated = block.token_count > block.budget
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=not violated,
            detail="budget exceeded" if violated else "",
            budget_violation=violated,
            context_tokens=block.token_count,
        )

    def _h_degraded(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        engine._retriever = _FailingRetriever()  # noqa: SLF001 - deliberate fault injection
        response = engine.chat(s.query_owner, s.query_text, now=clock.tick())
        success = response.degraded and bool(response.text)
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=success,
            detail="" if success else "no response on failure",
            degraded_success=success,
            latency_ms=response.latency_ms,
        )

    def _h_ignore(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        stored = engine.memories(s.query_owner)
        passed = len(stored) == 0
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=passed,
            detail="temporary text was stored" if not passed else "",
        )

    def _h_expiry(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        owner = s.query_owner
        for record in engine.memories(owner):
            engine.governance.set_retention(
                owner,
                record.id,
                RetentionPolicy.FIXED_EXPIRY,
                expires_at=record.created_at,
                now=clock.tick(),
            )
        engine.run_fade(now=clock.tick(), owner_id=owner)
        _, block, _ = engine.retrieve(owner, s.query_text, now=clock.tick())
        leaked = _contains_any(block.text, s.forbidden)
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=not leaked,
            detail="expired memory leaked" if leaked else "",
            leaked=leaked,
            context_tokens=block.token_count,
        )

    def _h_injection(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        _, block, _ = engine.retrieve(s.query_owner, s.query_text, now=clock.tick())
        quoted = OPEN_TAG in block.text and _contains_any(block.text, s.relevant)
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=quoted,
            detail="" if quoted else "injection not present as quoted data",
            context_tokens=block.token_count,
        )

    def _h_duplicate(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        count = len(engine.memories(s.query_owner))
        passed = count == 1
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=passed,
            detail=f"expected 1 memory, found {count}" if not passed else "",
        )

    def _h_import(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        rejected = False
        try:
            engine.governance.import_(s.query_owner, _MALFORMED_IMPORT)
        except ImportRejectedError:
            rejected = True
        clean = len(engine.memories(s.query_owner)) == 0
        passed = rejected and clean
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=passed,
            detail="" if passed else "malformed import was not fully rejected",
        )

    def _h_delete_export(self, engine: ChatEngine, s: Scenario, clock: _Clock) -> ScenarioOutcome:
        owner = s.query_owner
        engine.governance.delete_all(owner, now=clock.tick())
        exported = engine.governance.export(owner)
        leaked = _contains_any(exported, s.forbidden) or bool(exported.strip())
        return ScenarioOutcome(
            id=s.id,
            category=s.category.value,
            kind=s.kind.value,
            passed=not leaked,
            detail="export not empty after delete-all" if leaked else "",
            leaked=leaked,
        )


_HANDLERS = {
    Kind.RECALL: BenchRunner._h_recall,
    Kind.CORRECTION: BenchRunner._h_correction,
    Kind.FORGET: BenchRunner._h_forget,
    Kind.CROSS_OWNER: BenchRunner._h_cross_owner,
    Kind.SECRET: BenchRunner._h_secret,
    Kind.BUDGET: BenchRunner._h_budget,
    Kind.DEGRADED: BenchRunner._h_degraded,
    Kind.IGNORE: BenchRunner._h_ignore,
    Kind.EXPIRY: BenchRunner._h_expiry,
    Kind.INJECTION: BenchRunner._h_injection,
    Kind.DUPLICATE: BenchRunner._h_duplicate,
    Kind.IMPORT: BenchRunner._h_import,
    Kind.DELETE_EXPORT: BenchRunner._h_delete_export,
}


def _contains_any(text: str, needles: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)
