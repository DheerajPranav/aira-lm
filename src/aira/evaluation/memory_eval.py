"""Memory-conditioned evaluation: does retrieved memory help the current checkpoint?

Runs controlled tasks through the real memory stack with Aira Core as the generation
backend, comparing three baselines: no-memory, Aira Memory and full-history. It measures
two different things and keeps them apart:

- **context availability** — did the expected fact reach the backend's context? (retrieval)
- **generation adherence** — did the model reproduce it in its output? (generation)

This separation is the point: the untrained tiny checkpoint is not expected to reproduce
facts, so generation adherence will be low regardless — that is reported honestly, while
retrieval's contribution is shown at the context boundary. No LLM judge, no frontier
comparison, no cherry-picking.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from aira.chat.backend import GenerationBackend, GenerationRequest
from aira.config import AiraConfig
from aira.core.backend import TinyTransformerBackend
from aira.core.model import AiraCore
from aira.evaluation import metrics
from aira.memory.capture import CaptureService, Speaker
from aira.memory.guard import default_guard
from aira.memory.ranking import (
    ByteTokenizer,
    DecayParams,
    Ranker,
    RankingWeights,
    compose_memory_context,
)
from aira.memory.recall import build_retriever
from aira.memory.recall.interface import Retriever
from aira.memory.vault import MemoryRepository, connect

_BASE_TIME = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
_BASELINES = ("no_memory", "aira", "full_history")


@dataclass(frozen=True, slots=True)
class MemoryTask:
    """A controlled task: some setup turns, a query, and an expected/forbidden fact."""

    id: str
    kind: str  # "factual" | "correction" | "forgetting"
    setup: tuple[tuple[str, str], ...]  # (owner, message)
    query_owner: str
    query_text: str
    expected: str | None = None
    forbidden: str | None = None


def default_memory_tasks() -> list[MemoryTask]:
    """The built-in controlled tasks."""
    a = "owner-a"
    return [
        MemoryTask(
            "editor_fact", "factual", ((a, "my editor is vim"),), a, "what is my editor", "vim"
        ),
        MemoryTask(
            "project_fact",
            "factual",
            ((a, "i'm working on project falcon"),),
            a,
            "what project am i working on",
            "falcon",
        ),
        MemoryTask(
            "editor_correction",
            "correction",
            ((a, "my editor is vim"), (a, "actually my editor is emacs")),
            a,
            "what is my editor",
            expected="emacs",
            forbidden="vim",
        ),
        MemoryTask(
            "editor_forgotten",
            "forgetting",
            ((a, "my editor is vim"), (a, "forget my editor")),
            a,
            "what is my editor",
            forbidden="vim",
        ),
    ]


@dataclass(frozen=True, slots=True)
class BaselineMetrics:
    """Aggregated metrics for one baseline."""

    context_availability: float
    generation_adherence: float
    correction_adherence: float
    forgotten_nondisclosure: float
    avg_context_tokens: float
    avg_latency_ms: float

    def canonical(self) -> dict[str, float]:
        """Deterministic (latency-free) view."""
        return {
            "context_availability": self.context_availability,
            "generation_adherence": self.generation_adherence,
            "correction_adherence": self.correction_adherence,
            "forgotten_nondisclosure": self.forgotten_nondisclosure,
            "avg_context_tokens": self.avg_context_tokens,
        }


@dataclass(frozen=True, slots=True)
class MemoryEvalReport:
    """The result of a memory-conditioned evaluation run."""

    schema_version: int
    model: dict[str, Any]
    task_count: int
    baselines: dict[str, BaselineMetrics]
    ablation: dict[str, float]
    conclusion: str

    def canonical(self) -> dict[str, Any]:
        """A deterministic view for reproducibility checks (excludes latency)."""
        return {
            "schema_version": self.schema_version,
            "model": self.model,
            "task_count": self.task_count,
            "baselines": {name: m.canonical() for name, m in self.baselines.items()},
            "ablation": self.ablation,
            "conclusion": self.conclusion,
        }

    def to_dict(self) -> dict[str, Any]:
        """Full JSON-safe report including latency."""
        data = self.canonical()
        data["latency_ms"] = {name: m.avg_latency_ms for name, m in self.baselines.items()}
        return data

    def to_markdown(self) -> str:
        """A readable Markdown summary."""
        lines = ["# Memory-Conditioned Evaluation", ""]
        lines.append(f"- Model: {self.model}")
        lines.append(f"- Tasks: {self.task_count}")
        lines.append("")
        lines.append(
            "| baseline | ctx_avail | gen_adhere | correction | forgot_nondisc | ctx_tokens |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|")
        for name in _BASELINES:
            m = self.baselines[name]
            lines.append(
                f"| {name} | {m.context_availability:.2f} | {m.generation_adherence:.2f} | "
                f"{m.correction_adherence:.2f} | {m.forgotten_nondisclosure:.2f} | "
                f"{m.avg_context_tokens:.1f} |"
            )
        lines.append("")
        lines.append("## Ranking ablation (context availability)")
        for name, value in self.ablation.items():
            lines.append(f"- {name}: {value:.2f}")
        lines.append("")
        lines.append("## Conclusion")
        lines.append(self.conclusion)
        return "\n".join(lines) + "\n"


class _Clock:
    def __init__(self) -> None:
        self._t = _BASE_TIME

    def tick(self) -> datetime:
        self._t += timedelta(minutes=1)
        return self._t


def _contains(text: str, needle: str | None) -> bool:
    return needle is not None and needle.lower() in text.lower()


class MemoryConditionedEvaluator:
    """Evaluates whether retrieved memory helps a given Aira Core checkpoint."""

    def __init__(
        self,
        config: AiraConfig,
        model: AiraCore,
        *,
        backend: GenerationBackend | None = None,
        seed: int = 0,
        checkpoint: str | None = None,
        max_new_tokens: int = 24,
    ) -> None:
        """Wire the evaluator over a config and a model (defaults to a CPU tiny backend)."""
        self._cfg = config
        self._model = model
        self._seed = seed
        self._checkpoint = checkpoint
        self._backend = backend or TinyTransformerBackend(
            model, device="cpu", max_new_tokens=max_new_tokens
        )
        self._budget_tok = ByteTokenizer()
        self._weights = RankingWeights.from_config(config.retrieval)
        self._decay = DecayParams.from_config(config.decay)

    def run(self, tasks: Sequence[MemoryTask] | None = None) -> MemoryEvalReport:
        """Run all tasks across the three baselines and return a report."""
        cases = list(tasks) if tasks is not None else default_memory_tasks()
        acc: dict[str, _Accumulator] = {name: _Accumulator() for name in _BASELINES}
        ranker = Ranker(self._weights, self._decay)

        for task in cases:
            for name in _BASELINES:
                ctx_text, facts = self._context_for(name, task, ranker)
                start = time.perf_counter()
                output = self._backend.generate(
                    GenerationRequest(task.query_text, ctx_text, tuple(facts))
                )
                latency = (time.perf_counter() - start) * 1000
                acc[name].record(task, ctx_text, output, latency, self._budget_tok.count(ctx_text))

        baselines = {name: acc[name].summarize() for name in _BASELINES}
        ablation = {
            "default_ranking": self._availability(cases, ranker),
            "lexical_only": self._availability(cases, Ranker(_lexical_only_weights(), self._decay)),
        }
        return MemoryEvalReport(
            schema_version=1,
            model=self._model_info(),
            task_count=len(cases),
            baselines=baselines,
            ablation=ablation,
            conclusion=_conclude(baselines),
        )

    # --- context construction per baseline -----------------------------------------

    def _context_for(
        self, baseline: str, task: MemoryTask, ranker: Ranker
    ) -> tuple[str, list[str]]:
        if baseline == "no_memory":
            return "", []
        repo, retriever, now = self._setup(task)
        if baseline == "full_history":
            records = repo.list_memories(task.query_owner, limit=1_000_000)
            facts = [r.content for r in records]
            return "\n".join(facts), facts
        return self._aira_context(retriever, ranker, task.query_owner, task.query_text, now)

    def _aira_context(
        self, retriever: Retriever, ranker: Ranker, owner: str, query: str, now: datetime
    ) -> tuple[str, list[str]]:
        results = retriever.search(owner, query, limit=50)
        ranked = ranker.rank(results, now=now)
        block = compose_memory_context(
            ranked,
            budget=self._cfg.memory.context_token_budget,
            top_k=self._cfg.memory.top_k,
            tokenizer=self._budget_tok,
        )
        by_id = {rm.memory.id: rm.memory for rm in ranked}
        facts = [by_id[item.memory_id].content for item in block.items]
        return block.text, facts

    def _setup(self, task: MemoryTask) -> tuple[MemoryRepository, Retriever, datetime]:
        repo = MemoryRepository(connect(":memory:"))
        capture = CaptureService(default_guard(), repo)
        clock = _Clock()
        for owner, message in task.setup:
            capture.process(owner, Speaker.USER, message, now=clock.tick())
        return repo, build_retriever(repo), clock.tick()

    def _availability(self, tasks: Sequence[MemoryTask], ranker: Ranker) -> float:
        checkable = [t for t in tasks if t.expected is not None]
        if not checkable:
            return 0.0
        hits = 0
        for task in checkable:
            repo, retriever, now = self._setup(task)
            ctx_text, _ = self._aira_context(
                retriever, ranker, task.query_owner, task.query_text, now
            )
            hits += int(_contains(ctx_text, task.expected))
        return round(metrics.rate(hits, len(checkable)), 6)

    def _model_info(self) -> dict[str, Any]:
        return {
            "parameter_count": self._model.parameter_count(),
            "embedding_dim": self._cfg.model.embedding_dim,
            "layers": self._cfg.model.layers,
            "context_length": self._cfg.model.context_length,
            "checkpoint": self._checkpoint,
            "seed": self._seed,
        }


@dataclass(slots=True)
class _Accumulator:
    context_avail: list[float] = field(default_factory=list)
    gen_adherence: list[float] = field(default_factory=list)
    correction: list[float] = field(default_factory=list)
    nondisclosure: list[float] = field(default_factory=list)
    ctx_tokens: list[float] = field(default_factory=list)
    latency: list[float] = field(default_factory=list)

    def record(
        self, task: MemoryTask, ctx: str, output: str, latency_ms: float, ctx_tokens: int
    ) -> None:
        self.ctx_tokens.append(float(ctx_tokens))
        self.latency.append(latency_ms)
        if task.expected is not None:
            self.context_avail.append(float(_contains(ctx, task.expected)))
            self.gen_adherence.append(float(_contains(output, task.expected)))
        if task.kind == "correction":
            corrected = _contains(output, task.expected) and not _contains(output, task.forbidden)
            self.correction.append(float(corrected))
        if task.kind == "forgetting":
            self.nondisclosure.append(float(not _contains(output, task.forbidden)))

    def summarize(self) -> BaselineMetrics:
        return BaselineMetrics(
            context_availability=round(metrics.mean(self.context_avail), 6),
            generation_adherence=round(metrics.mean(self.gen_adherence), 6),
            correction_adherence=round(metrics.mean(self.correction), 6),
            forgotten_nondisclosure=round(metrics.mean(self.nondisclosure), 6),
            avg_context_tokens=round(metrics.mean(self.ctx_tokens), 2),
            avg_latency_ms=round(metrics.mean(self.latency), 3),
        )


def _lexical_only_weights() -> RankingWeights:
    return RankingWeights(
        lexical=1.0,
        importance=0.0,
        confidence=0.0,
        recency=0.0,
        reinforcement=0.0,
        project=0.0,
        kind=0.0,
        decay_penalty=0.0,
    )


def _conclude(baselines: dict[str, BaselineMetrics]) -> str:
    aira = baselines["aira"]
    none = baselines["no_memory"]
    context_helps = aira.context_availability > none.context_availability
    gen_gap = aira.context_availability - aira.generation_adherence
    parts = []
    if context_helps:
        parts.append(
            f"Retrieval places the expected fact in context for Aira Memory "
            f"(context_availability={aira.context_availability:.2f}) versus "
            f"{none.context_availability:.2f} with no memory."
        )
    else:
        parts.append("Retrieval did not improve context availability on these tasks.")
    if gen_gap > 0.1:
        parts.append(
            f"The current (untrained) checkpoint does not reproduce those facts "
            f"(generation_adherence={aira.generation_adherence:.2f}); generation-side "
            f"benefit is inconclusive at this scale — a training limitation, not a retrieval one."
        )
    else:
        parts.append(
            f"Generation adherence is {aira.generation_adherence:.2f}; "
            f"interpret with the small task set in mind."
        )
    return " ".join(parts)
