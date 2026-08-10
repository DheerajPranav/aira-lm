"""Adapter that lets Aira Core serve as a chat generation backend.

Implements the chat ``GenerationBackend`` protocol over an :class:`AiraCore` model and the
byte tokenizer. It works with an untrained model (output is meaningless but deterministic
under greedy decoding) so the rest of the system can be tested without a checkpoint. No
language-quality claim is made here.
"""

from __future__ import annotations

import torch

from aira.chat.backend import GenerationRequest
from aira.core.model import AiraCore
from aira.core.tokenizer import ByteTokenizer
from aira.device import select_device


class TinyTransformerBackend:
    """A :class:`~aira.chat.backend.GenerationBackend` backed by Aira Core."""

    def __init__(
        self,
        model: AiraCore,
        tokenizer: ByteTokenizer | None = None,
        *,
        device: str | None = None,
        max_new_tokens: int = 32,
    ) -> None:
        """Wrap a model and tokenizer, moving the model to the selected device."""
        self._device = device or select_device()
        self._model = model.to(self._device)
        self._model.eval()
        self._tok = tokenizer or ByteTokenizer()
        self._max_new_tokens = max_new_tokens

    def generate(self, request: GenerationRequest) -> str:
        """Greedy-decode a short continuation of the composed prompt."""
        prompt = self._build_prompt(request)
        # Reserve room for the new tokens within the model's context window.
        keep = self._model.context_length - self._max_new_tokens
        ids = self._tok.encode(prompt)[-max(keep, 1) :]
        idx = torch.tensor([ids], dtype=torch.long, device=self._device)
        out = self._model.greedy_generate(idx, self._max_new_tokens)
        new_ids = out[0, len(ids) :].tolist()
        return self._tok.decode(new_ids)

    def _build_prompt(self, request: GenerationRequest) -> str:
        parts = []
        if request.memory_context:
            parts.append(request.memory_context)
        parts.append(f"User: {request.message}")
        parts.append("Assistant:")
        return "\n".join(parts)
