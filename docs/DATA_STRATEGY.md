# Data Strategy

> Design reference for how Aira Core is trained and how memory-conditioned behaviour
> is evaluated. **Not yet implemented.** The generator and datasets described here are
> built in Steps 11–13; this document locks the design so those steps only execute it.
> It introduces no runtime code and makes no claim about model quality.

## 1. Why synthetic-first is the right choice, not a fallback

Aira Core is a **5–10M-parameter byte-level** model (vocabulary 256). It will never be
fluent, and that is intentional (`docs/MISSION.md`, `MODEL_CARD.md`). The model exists
only to answer one narrow research question:

> When a retrieved memory is placed in the context, does generation change the way it
> should — more than it would from the weights alone?

That goal does not need a large or realistic corpus. It needs a **small, closed,
fully-controlled distribution** where every fact's ground truth is known. Generating
that distribution ourselves is better than scraping real text on every axis that
matters to this project:

| Concern | Real corpus | Synthetic closed-domain corpus |
|---|---|---|
| Tiny model can fit it | No (open vocabulary, long tail) | Yes (bounded grammar + entities) |
| Ground truth for evaluation | Unknown / needs labelling | Known by construction |
| Offline, no auto-download | Hard (violates a project constraint) | Trivially satisfied |
| Licensing / provenance | Unresolved | None — we author it |
| Contains the exact facts under test | Rarely | Yes, or deliberately held out |
| Reproducible byte-for-byte | No | Yes (seeded) |

The generator's output **is** the dataset. There is nothing to collect: we write a
generator, run it, and train on what it emits.

## 2. What "the data" actually is

Two artifacts, both produced by one seeded generator:

1. **A generator** — a small template grammar plus a fixed pool of invented entities
   (people, projects, tools, preferences, places). Deterministic given a seed.
2. **Its outputs** — plain UTF-8 text files under `data/` (git-ignored). These are the
   training corpus and the evaluation task sets.

Because the tokenizer is byte-level, there is **no tokenizer training** and **no
out-of-vocabulary problem**: invented names such as `falcon` or `orion` are simply
bytes. This is a core reason a tiny model can cope with the domain.

### 2.1 Training corpus (teaches the domain's shape)

Short, declarative sentences that establish the grammar and the relationships the
model must be able to represent:

```
User alex prefers dark mode.
User priya is working on project falcon.
alex uses the fish shell.
The version of tool orion is 3.2.
priya deploys on fridays.
```

The statement kinds map directly onto the memory taxonomy already defined in
`docs/ARCHITECTURE.md`:

| Statement pattern | Memory kind | Example |
|---|---|---|
| "X prefers Y" | preference | alex prefers dark mode |
| "X is working on project P" | semantic / project | priya → falcon |
| "The version of T is V" | semantic | orion → 3.2 |
| "Always do Z" | instruction | always answer briefly |
| "X did E on D" | episodic | alex merged pr-14 on monday |

### 2.2 Evaluation task triples (measure the memory contrast)

Each evaluation item is a `(memory, prompt, expected)` triple with a deterministic,
checkable answer — a short span, so scoring needs no LLM judge (`docs/EVALUATION_PLAN.md`):

```json
{"memory": "alex prefers dark mode",
 "prompt": "What theme does alex prefer?",
 "expected": "dark mode",
 "kind": "preference",
 "owner_id": "u_alex"}
```

The same triples drive the three baselines the evaluation plan requires:

- **No-memory** — prompt only.
- **Aira Memory** — prompt + the retrieved memory, composed through the real pipeline.
- **Full-history** — prompt + all prior turns (where practical), as an upper-bound reference.

## 3. The central design constraint: defeat the memorization confound

The one way synthetic data can lie: if a fact is in both training and evaluation, the
model answers correctly **from its weights**, and "memory helped" looks true even when
retrieval did nothing. The whole result would be an artefact.

Mitigation — **held-out entity slots**:

- Partition the entity pool into a **train split** and a **held-out split**. Held-out
  people/projects/tools/values **never appear in the training corpus**.
- Build the primary evaluation set entirely from **held-out** entities. For those
  items the answer is *unavailable from the weights* — the only path to a correct
  answer is the memory placed in context.
- Keep a secondary "seen" set (train-split entities) to quantify how much the model
  memorized, as a control.

This yields the honest comparison Step 13 asks for: **memory vs no-memory on facts the
model could not have learned**. It is also the natural place for the ranking-signal
ablations mentioned in Step 13.

## 4. Sizing

Deliberately small; the generator can produce more on demand.

| Purpose | Step | Approx size | Notes |
|---|---|---|---|
| Overfit smoke fixture | 12 | ~50–200 KB | Prove `loss decreases`, deterministic greedy generation, checkpoint round-trip. Minutes on M2 CPU/MPS. |
| Domain training corpus | 12–13 | ~2–8 MB | Enough repetition of the closed grammar for the model to represent relations. |
| Evaluation task sets | 13 | ~200–1000 triples | Split into held-out (primary) and seen (control). |

Rules of thumb, not targets: exact sizes are chosen empirically at Step 12 against
measured loss and peak memory, and recorded in `docs/BUILD_STATUS.md`. Nothing here is
tuned for language quality — only for making the memory contrast measurable within the
8 GB / M2 budget.

## 5. Determinism, provenance and safety

- **Seeded.** Every corpus and task set is produced from an explicit seed
  (`runtime.seed`), so training and evaluation are byte-for-byte reproducible
  (invariant 12).
- **Provenance.** The generator version and seed are recorded alongside outputs; the
  data section of `MODEL_CARD.md` is updated with exact sizes and seeds once generated.
- **Offline.** No network access, no automatic downloads (project constraint).
- **No secrets.** The grammar emits only invented, non-sensitive values. If any
  real-text scaffold (§6) is ever used, it passes through Aira Guard's detectors
  before training, so the corpus cannot carry credentials (invariant 7).
- **Owner scoping.** Evaluation triples carry an `owner_id`, so cross-owner retrieval
  scenarios (owner A asks for owner B's fact) are expressible directly — feeding the
  zero-tolerance cross-owner-leakage checks in Step 10/13.

## 6. Optional real-text scaffold (deferred, not required)

If we later want the model to read slightly more like English, we may mix in a small
**public-domain, user-supplied, local** text file (for example a Project Gutenberg
book the user places in `data/` themselves). Constraints:

- Manually supplied and offline — never auto-downloaded.
- Public-domain or otherwise clearly permitted; provenance noted in `MODEL_CARD.md`.
- Guard-scanned before use.
- Clearly a fluency scaffold, not part of the fact distribution under test.

The research question does not depend on this; treat it as a later, justified add-on.

## 7. Proposed layout (target, created in Steps 11–13)

```text
src/aira/core/data/
  __init__.py
  grammar.py        # templates + entity pools, train/held-out split
  generate.py       # CLI: emit corpus + task sets from a seed
data/               # git-ignored generator output
  train.txt
  smoke.txt
  eval_heldout.jsonl
  eval_seen.jsonl
benchmarks/
  memory_conditioned/   # task sets promoted into Aira Bench (Step 13)
```

## 8. What this strategy does and does not claim

- **Does:** give a reproducible, offline, license-clean way to train the tiny model
  and to measure whether retrieved memory changes its output on facts it never saw.
- **Does not:** claim language quality, general capability, or that results transfer
  to larger models or real corpora. Step 13 must report negative or inconclusive
  results honestly.

## 9. Open decisions

| Decision | Resolve by | Notes |
|---|---|---|
| Grammar breadth (how many relation types) | Step 11 | Start minimal (preference + version + project); expand only if the contrast is measurable. |
| Held-out fraction of the entity pool | Step 12 | Large enough for a stable eval set; small enough to keep the domain learnable. |
| Corpus size vs measured loss / peak memory | Step 12 | Chosen empirically, recorded as evidence. |
| Whether to include the real-text scaffold | Step 13+ | Default: no. |
| Promotion of task sets into Aira Bench format | Step 13 | Align JSONL schema with Step 10's benchmark schema. |

## 10. Relationship to the plan

This document informs Steps **11** (Aira Core / tokenizer — byte-level makes the
closed vocabulary free), **12** (training on the generated corpus + smoke fixture) and
**13** (memory-conditioned evaluation with held-out slots and the three baselines). It
is a design reference only; see `PROJECT_PLAN.md` for stage gates and
`docs/EVALUATION_PLAN.md` for the metrics these datasets feed.
