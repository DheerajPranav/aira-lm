# Master Build Prompt

Use this only as a project overview. Do **not** execute every stage in one Claude Code session.

You are the lead AI research and systems engineer for Aira LM.

Build a local-first, memory-native small language model with two independent systems:

- Aira Core: compact decoder-only transformer
- Aira Memory: selective, secure, auditable memory runtime

The repository must prioritize correctness, privacy, evaluation and explainability over breadth.

Read `CLAUDE.md` and all imported documents. Execute the numbered files in `prompts/` sequentially. Never begin the next step until the current prompt’s tests and completion criteria pass and `docs/BUILD_STATUS.md` has been updated.

The first release is a production-minded local reference implementation, not a production-ready hosted service.

At every step:

1. inspect existing work
2. preserve useful files
3. implement only the requested slice
4. add deterministic offline tests
5. run tests, lint and type checks
6. update ADRs
7. record evidence in BUILD_STATUS
8. stop
