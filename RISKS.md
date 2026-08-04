# Risks

> Stage 00 deliverable. Known risks with likelihood, impact, and the mitigation or
> stage that addresses each. Security-relevant risks map to hard invariants and to
> zero-tolerance benchmark metrics.

Scale: Likelihood / Impact ∈ {Low, Medium, High}.

## Engineering & environment

| ID | Risk | L | I | Mitigation | Owner stage |
|---|---|---|---|---|---|
| R1 | System interpreter is Python 3.13 while target is 3.12; accidental 3.13 build | High | Medium | `uv` pins a 3.12 toolchain; CI/`aira doctor` reports interpreter version; document in README | 01 |
| R2 | Dependency drift / unpinned versions break reproducibility | Medium | Medium | Pin versions + lockfile; document every dependency; `uv sync` in gate | 01 |
| R3 | FTS5 unavailable on some SQLite builds | Low | Medium | Runtime detection + deterministic BM25 fallback; record availability | 06 |
| R4 | M2 8 GB memory exhaustion during model/train | Medium | High | Tiny configs, bounded batches, smoke modes, peak-memory tracking | 11, 12 |
| R5 | Non-deterministic tests (clocks, hashing, ordering) | Medium | High | Fixed clocks, seeded RNG, deterministic hashing + tie-breaks | 02, 06, 07, 10 |
| R6 | Circular imports / blurred module boundaries | Medium | Medium | Enforce dependency direction; persistence/retrieval/ranking/policy/model separated | 01–07 |

## Security & privacy (map to invariants / zero-tolerance metrics)

| ID | Risk | L | I | Invariant | Mitigation | Owner stage |
|---|---|---|---|---|---|---|
| R7 | Cross-owner leakage | Medium | High | 1 | Mandatory `owner_id` in every repository method; owner-scoped SQL in one layer; adversarial two-owner tests; **leakage = 0** | 04, 06, 08, 10 |
| R8 | Forgotten/expired/superseded memory still retrievable | Medium | High | 2 | Inactive-state filtering before ranking; index cleanup; export filters; exact-match test; **forgotten leakage = 0** | 04, 06, 07, 10 |
| R9 | Secret persisted in content, logs, exceptions, audit, or export | Medium | High | 7 | Aira Guard before evaluation; multiple detectors; redacted previews only; audit omits content; **secret persistence = 0** | 03, 04, 10 |
| R10 | Stored prompt injection promoted to instructions | Medium | High | 8 | Delimited untrusted-memory format; never merge memory into system policy; injection benchmark | 07, 10 |
| R11 | Context-budget overflow crowds/rejects the prompt | Medium | Medium | 10 | Exact byte-token budget with real tokenizer; top-k + size limits; **budget violations = 0** | 07, 10 |
| R12 | Feedback poisoning creates false durable preference | Low | Medium | 5, 9 | Evidence thresholds; explicit-source priority; no auto-reinforcement on mere retrieval | 05, 09 |
| R13 | Hard deletion incomplete (content survives in audit/index/export) | Low | High | 2, 7 | Single transaction for status+event; audit content omission; export filters; exact test | 04, 09 |
| R14 | Malformed/hostile import corrupts store or smuggles secrets | Low | Medium | 5, 7 | Schema validation, size limits, owner rebinding, guard scan, atomic rollback | 09 |
| R15 | Interrupted write leaves state without audit (or vice versa) | Low | High | 11 | One transaction for state + event; failure-injection rollback test | 04 |

## Project & governance

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R16 | Scope creep — running many stages at once | Medium | Medium | One numbered prompt per session; stop after each gate; update BUILD_STATUS |
| R17 | Overstated claims (production/quality/security) | Medium | High | Invariant 12: no claim without a repeatable test; honest README/MODEL_CARD |
| R18 | Public repo published before license decision | Medium | Low | No `LICENSE` invented; all-rights-reserved by default until user chooses |
| R19 | Public docs imply a finished system | Medium | Medium | README + Pages landing page state Stage 00 status plainly; roadmap shown as future |
| R20 | Encryption / hosted-production expectations from readers | Low | Medium | Threat model out-of-scope section + `PRODUCTION_GAP.md` (Step 14) |

## Residual risk statement

At Stage 00 no runtime code exists, so security controls are **planned, not
verified**. The zero-tolerance metrics (cross-owner leakage, forgotten leakage,
secret persistence, context-budget violations) become measurable only at Step 10 and
must read exactly 0 there. Until then, all security properties are design intent.
