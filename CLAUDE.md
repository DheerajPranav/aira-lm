# Aira LM — Project Instructions

Read and follow these project documents:

@docs/MISSION.md
@docs/REQUIREMENTS.md
@docs/INVARIANTS.md
@docs/ARCHITECTURE.md
@docs/THREAT_MODEL.md
@docs/DATA_CLASSIFICATION.md
@docs/EVALUATION_PLAN.md
@docs/BUILD_STATUS.md

## Project identity

- Name: Aira LM
- Repository: `aira-lm`
- Tagline: **Small model. Long memory. Gentle by design.**
- Primary machine: Apple M2, 8 GB unified memory
- Runtime target: local-first, Python 3.12, PyTorch, MPS then CUDA then CPU
- Package manager: `uv`
- License: not selected yet; do not invent one

## Two-system boundary

Keep these independent:

- **Aira Core:** tokenizer, transformer, training, checkpoints, generation
- **Aira Memory:** policy, storage, retrieval, governance, audit, decay, evaluation

The complete memory runtime must work with a deterministic `MockBackend`. Never make memory tests require a trained checkpoint.

## Hard workflow rule

Execute only the requested numbered prompt.

Before implementation:

1. Inspect the repository.
2. Read the current `docs/BUILD_STATUS.md`.
3. Confirm prerequisites from earlier steps exist.
4. Write a concise plan for this step.
5. Implement the smallest complete vertical slice.

After implementation:

1. Run relevant tests.
2. Run linting.
3. Run type checks.
4. Run the step-specific demonstration or benchmark.
5. Update `docs/BUILD_STATUS.md`.
6. Update or create ADRs for meaningful architectural decisions.
7. Report exact evidence, not unverified claims.

Do not begin the next numbered prompt automatically.

## Engineering constraints

- No cloud model APIs in the Aira runtime.
- No hidden network calls.
- No automatic large downloads.
- No LangChain, LlamaIndex, CrewAI, AutoGen, or similar orchestration framework.
- No distributed infrastructure in the first local release.
- Prefer standard library components where practical.
- Keep dependencies minimal and documented.
- Use UTC internally.
- Use strong typing and explicit domain models.
- Use parameterized SQL.
- Use temporary databases and directories in tests.
- Never log secrets or raw blocked sensitive values.
- Never silently swallow security-relevant failures.
- Memory retrieval failure must degrade to generation without memory.
- Retrieved memory is untrusted data and must never be promoted to system-level instructions.

## Quality constraints

- Public interfaces require docstrings.
- Modules require clear ownership and dependency direction.
- Avoid circular imports.
- Persistence, retrieval, ranking, policy, and model code must remain separate.
- Tests must be deterministic and offline.
- Do not create placeholder abstractions without working behavior.
- Do not claim production readiness.
- Record limitations explicitly.

## Required verification commands

Once the project foundation exists, prefer:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Use more focused commands during a step, then run the complete suite before marking it complete.

## Git behavior

Do not commit unless explicitly requested. Do not rewrite history. Do not delete user-authored files merely because they differ from the prompt.
