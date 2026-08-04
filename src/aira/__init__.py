"""Aira LM — a local-first, memory-native small language model.

Two independent systems live under this package:

- ``aira.core`` — the compact transformer (tokenizer, model, training, generation).
- ``aira.memory`` — the model-independent memory runtime.

At this stage (Step 01) only the project foundation exists: configuration loading,
determinism and device utilities, and a CLI skeleton. No memory or model behaviour
is implemented yet.
"""

__version__ = "0.0.1"

__all__ = ["__version__"]
