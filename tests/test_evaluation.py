"""Tests for Aira Bench: metrics, scenario schema, and the zero-tolerance gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from aira.config import load_config
from aira.evaluation import (
    BenchReport,
    BenchRunner,
    Category,
    default_scenarios,
    dump_jsonl,
    load_jsonl,
    scenario_from_dict,
    validate_scenario_dict,
)
from aira.evaluation.metrics import precision, recall, recall_at_k, reciprocal_rank

_CFG = load_config("configs/aira_tiny.toml")


@pytest.fixture(scope="module")
def report() -> BenchReport:
    outcomes = BenchRunner(_CFG).run()
    return BenchReport.from_outcomes(outcomes, _CFG)


# --- metric unit tests -------------------------------------------------------------


def test_precision() -> None:
    assert precision(["a", "b"], {"a"}) == 0.5
    assert precision([], set()) == 0.0


def test_recall() -> None:
    assert recall(["a"], {"a", "b"}) == 0.5
    assert recall([], set()) == 1.0  # nothing relevant -> trivially satisfied


def test_recall_at_k() -> None:
    assert recall_at_k(["a", "b", "c"], {"c"}, 2) == 0.0
    assert recall_at_k(["a", "c"], {"c"}, 2) == 1.0


def test_reciprocal_rank() -> None:
    assert reciprocal_rank(["a", "b", "c"], {"c"}) == pytest.approx(1 / 3)
    assert reciprocal_rank(["a"], {"z"}) == 0.0


# --- scenario schema ---------------------------------------------------------------


def test_default_scenarios_validate() -> None:
    for scenario in default_scenarios():
        validate_scenario_dict(scenario.to_dict())


def test_jsonl_round_trip() -> None:
    scenarios = default_scenarios()
    loaded = load_jsonl(dump_jsonl(scenarios))
    assert [s.to_dict() for s in loaded] == [s.to_dict() for s in scenarios]


def test_committed_fixture_matches_defaults() -> None:
    text = Path("benchmarks/scenarios.v1.jsonl").read_text(encoding="utf-8")
    loaded = load_jsonl(text)
    assert [s.to_dict() for s in loaded] == [s.to_dict() for s in default_scenarios()]


@pytest.mark.parametrize(
    "bad",
    [
        {"id": "x"},  # missing keys
        {
            "schema_version": 99,
            "id": "x",
            "category": "golden",
            "kind": "recall",
            "description": "d",
            "setup": [],
        },
        {
            "schema_version": 1,
            "id": "x",
            "category": "nope",
            "kind": "recall",
            "description": "d",
            "setup": [],
        },
    ],
)
def test_invalid_scenarios_raise(bad: dict[str, object]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - message varies by failure
        scenario_from_dict(bad)


def test_golden_and_adversarial_present() -> None:
    scenarios = default_scenarios()
    golden = [s for s in scenarios if s.category is Category.GOLDEN]
    adversarial = [s for s in scenarios if s.category is Category.ADVERSARIAL]
    assert golden and adversarial


# --- benchmark run -----------------------------------------------------------------


def test_all_scenarios_pass(report: BenchReport) -> None:
    assert report.scenario_count == len(default_scenarios())
    assert report.all_passed
    assert report.regressions() == []


@pytest.mark.parametrize(
    "metric",
    [
        "cross_owner_leakage_rate",
        "forgotten_leakage_rate",
        "secret_persistence_rate",
        "budget_violation_rate",
    ],
)
def test_zero_tolerance_is_zero(report: BenchReport, metric: str) -> None:
    assert report.zero_tolerance[metric] == 0.0


def test_correction_and_degraded_success(report: BenchReport) -> None:
    assert report.rates["correction_success_rate"] == 1.0
    assert report.rates["degraded_success_rate"] == 1.0


def test_aira_beats_no_memory(report: BenchReport) -> None:
    assert report.retrieval["aira"]["recall"] == 1.0
    assert report.retrieval["no_memory"]["recall"] == 0.0
    # Aira retrieves precisely — at least as precise as dumping full history
    assert report.retrieval["aira"]["precision"] >= report.retrieval["full_history"]["precision"]


def test_report_is_reproducible() -> None:
    a = BenchReport.from_outcomes(BenchRunner(_CFG).run(), _CFG)
    b = BenchReport.from_outcomes(BenchRunner(_CFG).run(), _CFG)
    assert a.canonical() == b.canonical()
