"""Aggregates scenario outcomes into a report with a zero-tolerance regression gate.

Produces a machine-readable dict/JSON and a readable Markdown summary. The four
zero-tolerance metrics must be exactly 0, and every shipped scenario must pass; otherwise
``regressions()`` is non-empty and the ``aira bench`` command exits non-zero.

Retrieval evaluation (does the right memory come back) is reported separately from
generation evaluation (does the model use it) — the latter arrives with Aira Core in
Step 13; this report covers retrieval and the security/lifecycle guarantees only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from aira.config import AiraConfig
from aira.evaluation import metrics
from aira.evaluation.runner import ScenarioOutcome

REPORT_SCHEMA_VERSION = 1
_BASELINES = ("no_memory", "aira", "full_history")
_METRIC_KEYS = ("precision", "recall", "recall_at_k", "mrr")


def _fraction_true(values: list[bool | None]) -> float:
    present = [bool(v) for v in values if v is not None]
    return metrics.rate(sum(present), len(present))


@dataclass(frozen=True, slots=True)
class BenchReport:
    """A complete benchmark report."""

    schema_version: int
    config: dict[str, Any]
    scenario_count: int
    retrieval: dict[str, dict[str, float]]
    rates: dict[str, float]
    zero_tolerance: dict[str, float]
    measurements: dict[str, float]
    outcomes: tuple[ScenarioOutcome, ...]

    @classmethod
    def from_outcomes(cls, outcomes: list[ScenarioOutcome], config: AiraConfig) -> BenchReport:
        """Aggregate scenario outcomes into a report."""
        recall_like = [o for o in outcomes if o.baselines is not None]

        def by_kind(kind: str) -> list[ScenarioOutcome]:
            return [o for o in outcomes if o.kind == kind]

        retrieval = {
            baseline: {
                key: round(
                    metrics.mean([o.baselines[baseline][key] for o in recall_like if o.baselines]),
                    6,
                )
                for key in _METRIC_KEYS
            }
            for baseline in _BASELINES
        }

        rates = {
            "correction_success_rate": _fraction_true(
                [o.correction_success for o in by_kind("correction")]
            ),
            "stale_retrieval_rate": _fraction_true([o.leaked for o in by_kind("correction")]),
            "degraded_success_rate": _fraction_true(
                [o.degraded_success for o in by_kind("degraded")]
            ),
        }
        zero_tolerance = {
            "cross_owner_leakage_rate": _fraction_true([o.leaked for o in by_kind("cross_owner")]),
            "forgotten_leakage_rate": _fraction_true([o.leaked for o in by_kind("forget")]),
            "secret_persistence_rate": _fraction_true(
                [o.secret_persisted for o in by_kind("secret")]
            ),
            "budget_violation_rate": _fraction_true(
                [o.budget_violation for o in by_kind("budget")]
            ),
        }
        measurements = {
            "avg_retrieval_latency_ms": round(
                metrics.mean([o.latency_ms for o in outcomes if o.latency_ms > 0]), 3
            ),
            "avg_context_tokens": round(
                metrics.mean([float(o.context_tokens) for o in outcomes if o.context_tokens > 0]), 2
            ),
            "memory_utilization": round(
                metrics.mean([o.precision for o in recall_like if o.precision is not None]), 6
            ),
        }
        return cls(
            schema_version=REPORT_SCHEMA_VERSION,
            config={
                "context_token_budget": config.memory.context_token_budget,
                "top_k": config.memory.top_k,
                "retrieval_backend": config.retrieval.backend,
            },
            scenario_count=len(outcomes),
            retrieval=retrieval,
            rates=rates,
            zero_tolerance=zero_tolerance,
            measurements=measurements,
            outcomes=tuple(outcomes),
        )

    @property
    def all_passed(self) -> bool:
        """Whether every scenario passed."""
        return all(o.passed for o in self.outcomes)

    def regressions(self) -> list[str]:
        """Return a list of regression descriptions; empty means the gate passes."""
        problems: list[str] = []
        for name, value in self.zero_tolerance.items():
            if value > 0:
                problems.append(f"zero-tolerance metric '{name}' is {value}, expected 0")
        for outcome in self.outcomes:
            if not outcome.passed:
                problems.append(f"scenario '{outcome.id}' failed: {outcome.detail}")
        return problems

    def canonical(self) -> dict[str, Any]:
        """A deterministic (latency-free) view for reproducibility checks."""
        return {
            "schema_version": self.schema_version,
            "config": self.config,
            "retrieval": self.retrieval,
            "rates": self.rates,
            "zero_tolerance": self.zero_tolerance,
            "memory_utilization": self.measurements["memory_utilization"],
            "outcomes": [o.canonical() for o in self.outcomes],
        }

    def to_dict(self) -> dict[str, Any]:
        """Full JSON-safe report including measurements."""
        data = self.canonical()
        data["scenario_count"] = self.scenario_count
        data["measurements"] = self.measurements
        return data

    def to_json(self) -> str:
        """Pretty-printed JSON of the full report."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        """A readable Markdown summary."""
        lines = ["# Aira Bench Report", ""]
        lines.append(f"- Scenarios: {self.scenario_count}")
        lines.append(f"- Config: {self.config}")
        lines.append(f"- All passed: {self.all_passed}")
        lines.append("")
        lines.append("## Zero-tolerance metrics (must be 0)")
        for name, value in self.zero_tolerance.items():
            lines.append(f"- {name}: {value}")
        lines.append("")
        lines.append("## Retrieval (mean over recall scenarios)")
        lines.append("| baseline | precision | recall | recall@k | mrr |")
        lines.append("|---|---:|---:|---:|---:|")
        for baseline in _BASELINES:
            m = self.retrieval[baseline]
            lines.append(
                f"| {baseline} | {m['precision']:.3f} | {m['recall']:.3f} | "
                f"{m['recall_at_k']:.3f} | {m['mrr']:.3f} |"
            )
        lines.append("")
        lines.append("## Other rates")
        for name, value in {**self.rates, **self.measurements}.items():
            lines.append(f"- {name}: {value}")
        lines.append("")
        lines.append("## Scenarios")
        lines.append("| id | kind | passed | detail |")
        lines.append("|---|---|:---:|---|")
        for o in self.outcomes:
            mark = "✓" if o.passed else "✗"
            lines.append(f"| {o.id} | {o.kind} | {mark} | {o.detail} |")
        regressions = self.regressions()
        if regressions:
            lines.append("")
            lines.append("## Regressions")
            lines.extend(f"- {r}" for r in regressions)
        return "\n".join(lines) + "\n"
