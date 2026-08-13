"""Aira Bench — versioned golden and adversarial evaluation.

Runs deterministic scenarios against the memory runtime, comparing no-memory, Aira Memory
and full-history baselines, and enforces the four zero-tolerance metrics (cross-owner
leakage, forgotten leakage, secret persistence, context-budget violation). No LLM judge is
used; relevance comes from known facts. Retrieval evaluation is reported separately from
generation evaluation (the latter arrives with Aira Core, Step 13).
"""

from __future__ import annotations

from aira.evaluation.memory_eval import (
    BaselineMetrics,
    MemoryConditionedEvaluator,
    MemoryEvalReport,
    MemoryTask,
    default_memory_tasks,
)
from aira.evaluation.report import BenchReport
from aira.evaluation.runner import BenchRunner, ScenarioOutcome
from aira.evaluation.scenarios import (
    SCHEMA_VERSION,
    Category,
    Kind,
    Scenario,
    default_scenarios,
    dump_jsonl,
    load_jsonl,
    scenario_from_dict,
    validate_scenario_dict,
)

__all__ = [
    "SCHEMA_VERSION",
    "BaselineMetrics",
    "BenchReport",
    "BenchRunner",
    "Category",
    "Kind",
    "MemoryConditionedEvaluator",
    "MemoryEvalReport",
    "MemoryTask",
    "Scenario",
    "ScenarioOutcome",
    "default_memory_tasks",
    "default_scenarios",
    "dump_jsonl",
    "load_jsonl",
    "scenario_from_dict",
    "validate_scenario_dict",
]
