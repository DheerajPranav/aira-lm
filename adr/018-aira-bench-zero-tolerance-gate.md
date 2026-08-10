# ADR: Deterministic benchmark with a zero-tolerance regression gate

- Status: Accepted
- Date: 2026-08-11
- Last reviewed: 2026-08-11

## Context

Step 10 turns the memory runtime's promised properties into repeatable evidence. The
evaluation plan requires golden and adversarial scenarios, retrieval metrics against
baselines, and four zero-tolerance security metrics that must equal 0. It also forbids an
LLM judge as the sole evaluator and requires determinism.

## Decision

1. **Deterministic scenario harness.** Each scenario runs on a fresh in-memory engine
   with a fixed, monotonically increasing clock. Scenarios are versioned data
   (`schema_version`), authored in code and committed as `benchmarks/scenarios.v1.jsonl`;
   a test asserts the fixture matches the code.
2. **Relevance by known facts, not a judge.** A retrieved memory is relevant if its
   content contains a scenario's declared substring; forbidden substrings must be absent
   from the composed context. No LLM is involved in scoring.
3. **Three baselines.** Retrieval metrics (precision, recall, recall@k, MRR) are computed
   for no-memory, Aira Memory and full-history, so Aira's value is visible (it matched
   full-history recall at higher precision, versus zero for no-memory).
4. **Four zero-tolerance metrics.** Cross-owner leakage, forgotten leakage, secret
   persistence and context-budget violation are measured directly from the cross-owner,
   forget, secret and budget scenarios and must be exactly 0.
5. **A regression gate.** `BenchReport.regressions()` is non-empty if any zero-tolerance
   metric exceeds 0 or any scenario fails; `aira bench` exits non-zero, failing the build.
6. **Reproducible reports.** The report separates deterministic metrics from latency
   measurements; a `canonical()` view (latency-free) is byte-stable across runs and is
   what the reproducibility test compares. Per-run reports are git-ignored; the versioned
   scenarios are committed.
7. **Retrieval vs generation evaluation kept separate.** This benchmark evaluates
   retrieval and the security/lifecycle guarantees. Generation evaluation (does the model
   *use* memory) arrives with Aira Core in Step 13 and is reported separately.

## Alternatives considered

- An LLM-as-judge for relevance. Rejected by the evaluation plan; also non-deterministic.
- Committing full per-run reports. Rejected: latency varies, causing churn; the
  deterministic `canonical()` view and the versioned scenarios are what matter.
- Embedding thresholds only (e.g. recall ≥ x). Kept the zero-tolerance-and-all-pass gate
  as primary; numeric thresholds can be layered on later.

## Consequences

- The memory runtime's security and lifecycle guarantees are now backed by a repeatable,
  build-failing gate; the four zero-tolerance metrics read 0 and every scenario passes.
- Scenario relevance is coarse (substring match), which suits known-fact scenarios but is
  not a general relevance model — acceptable and documented for this stage.

## Traceability

- Upholds invariants: 1, 2, 7, 10 via the four zero-tolerance metrics; 3 via the degraded
  scenario; 8 via the injection scenario; 12 by making every claim a repeatable test.
- Realized in stage 10; feeds Step 13 (memory-conditioned generation evaluation) and
  Step 14 (release verification re-runs the gate).

## Migration path

Add scenarios and bump the scenario `schema_version` as behaviour grows; layer numeric
regression thresholds onto the gate; reuse the same JSONL schema for Step 13's
generation-side tasks.
