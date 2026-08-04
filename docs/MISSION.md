# Mission

## Problem

Small language models lose useful context when a conversation or process ends. Simply increasing parameter count or context length is expensive and does not solve selective retention, correction, provenance, privacy, or forgetting.

## Mission

Build a local-first, memory-native small language model that investigates whether selective remembering can help compact models maintain useful long-term context.

## Research question

> Can a compact language model maintain long-horizon consistency through secure, selective, explainable remembering and responsible forgetting?

## Initial success definition

Aira succeeds initially when it can, with a deterministic mock backend:

1. Recognize a durable user fact or preference.
2. Reject temporary or unsafe information.
3. Store the approved memory with provenance.
4. Retrieve it only for the correct owner and relevant query.
5. Correct or supersede it.
6. Forget it so it cannot be retrieved.
7. Continue answering when memory is unavailable.
8. Explain in debug mode why a memory was stored or retrieved.
9. Prove these behaviors through offline tests and versioned evaluations.

## Non-goals for the first release

- Competing with frontier language models
- General-purpose autonomous agents
- Multi-agent orchestration
- Cloud deployment
- Automatic continual weight updates
- Storing every conversation
- Claiming human-like memory
- Claiming production readiness
