# Aira LM — Claude Code Launch Kit

**Tagline:** Small model. Long memory. Gentle by design.

This package is a build-control kit for creating Aira LM in Claude Code one verified stage at a time. It does not pretend that the project is already production-ready. It gives Claude Code the architecture, invariants, threat model, implementation sequence, and acceptance gates needed to build a robust local reference implementation.

## What Aira LM is

Aira LM has two independent but connected systems:

1. **Aira Core** — a compact decoder-only language model built directly in PyTorch.
2. **Aira Memory** — a model-independent runtime for selective remembering, updating, retrieval, forgetting, provenance, privacy, and evaluation.

The first useful milestone is **not** a highly fluent model. It is a complete and testable memory lifecycle that works with a deterministic mock backend.

## Emotional origin

Aira was inspired by the quiet strength of elephants and their association with enduring memory. The project investigates how a compact model can remember what matters without carrying everything forever.

The personal meaning remains subtle. The public engineering identity stands on its own.

## Before starting

You need:

- macOS or Linux
- Git
- Python 3.12
- `uv`
- Claude Code
- Internet access for Claude Code itself
- An M2 Mac with 8 GB RAM is the primary target, but CPU-only execution must remain supported

Check your tools:

```bash
chmod +x scripts/*.sh
./scripts/check_environment.sh
```

## Start the repository

Extract this kit, rename the folder if desired, and run:

```bash
cd aira-lm-claude-code-kit
git init
claude
```

Inside Claude Code, enter:

```text
Read CLAUDE.md, docs/BUILD_STATUS.md, and prompts/00_CONTROL_TOWER.md. Execute Step 0 only. Do not begin Step 1 until Step 0 is verified and BUILD_STATUS.md is updated.
```

Alternatively:

```bash
./scripts/start_step.sh 00
```

## Build sequence

Run one step at a time:

```text
00  Control tower and repository audit
01  Repository foundation
02  Memory schema and lifecycle
03  Aira Guard: privacy and secret filtering
04  Aira Vault and Aira Trail
05  Capture, extraction and deterministic evaluation
06  Aira Recall: FTS5/BM25 retrieval
07  Ranking and context construction
08  Chat integration and graceful degradation
09  Aira Fade and governance
10  Aira Bench: adversarial evaluation
11  Aira Core transformer
12  Training, checkpoints and generation
13  Memory-conditioned model evaluation
14  Release hardening
```

Use:

```bash
./scripts/list_steps.sh
./scripts/start_step.sh 01
./scripts/verify.sh
```

Do not run all stages simultaneously. Each stage must update `docs/BUILD_STATUS.md` with evidence.

## Claude Code operating rule

At the end of every step, Claude must report:

1. Files created or modified
2. Commands actually executed
3. Test, lint, and type-check results
4. Measured metrics
5. Known limitations
6. Any ADR created or changed
7. Exact command for the next step

A step is incomplete when tests were not run.

## Package map

```text
CLAUDE.md                   Persistent project instructions for Claude Code
docs/                       Requirements, architecture, threat model and status
prompts/                    One executable prompt per build stage
adr/                        Architecture decision records
configs/                    Initial local configuration
scripts/                    Environment, launch and verification helpers
references/                 Original memory-system architecture study
src/aira/                   Target package location
tests/                      Target tests
benchmarks/                 Golden and adversarial scenarios
```

## Important boundaries

Do not begin with:

- Kubernetes
- Temporal
- Redis
- PostgreSQL
- hosted embeddings
- a graph database
- multi-agent orchestration
- automatic reflection
- a learned memory-policy model

The local implementation must establish correct boundaries so those components can be introduced later without rewriting the system.

## First command

```bash
./scripts/start_step.sh 00
```
