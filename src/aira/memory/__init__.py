"""Aira Memory — the model-independent memory runtime.

The typed domain and lifecycle state machine live in :mod:`aira.memory.domain`
(Step 02). Aira Guard (Step 03), Aira Vault and Trail (Step 04), capture and evaluation
(Step 05), Aira Recall (Step 06), ranking and context (Step 07), and Aira Fade and
governance (Step 09) build on it in later steps. The full runtime is testable against a
deterministic mock backend and never requires a trained checkpoint.
"""

__all__: list[str] = []
