"""Autoregressive text generation: greedy, temperature and top-k sampling.

Greedy decoding (``temperature <= 0``) is fully deterministic. Sampling is reproducible
when a ``seed`` is given (a CPU generator drives ``multinomial``, so results are
device-independent). Generation never trains and makes no quality claim.
"""

from __future__ import annotations

import torch
from torch.nn import functional as F

from aira.core.model import AiraCore
from aira.core.tokenizer import ByteTokenizer
from aira.device import select_device


def _apply_top_k(logits: torch.Tensor, top_k: int) -> torch.Tensor:
    k = min(top_k, logits.size(-1))
    kth = torch.topk(logits, k, dim=-1).values[:, -1].unsqueeze(-1)
    return torch.where(logits < kth, torch.full_like(logits, float("-inf")), logits)


def generate(
    model: AiraCore,
    prompt: str,
    *,
    tokenizer: ByteTokenizer | None = None,
    max_new_tokens: int = 64,
    temperature: float = 1.0,
    top_k: int | None = None,
    seed: int | None = None,
    device: str | torch.device | None = None,
) -> str:
    """Generate a continuation of ``prompt`` and return only the newly generated text."""
    tok = tokenizer or ByteTokenizer()
    dev = device or select_device()
    model = model.to(dev)
    model.eval()

    generator = torch.Generator().manual_seed(seed) if seed is not None else None
    ids = tok.encode(prompt)
    idx = torch.tensor([ids], dtype=torch.long, device=dev)

    with torch.no_grad():
        for _ in range(max_new_tokens):
            conditioned = idx[:, -model.context_length :]
            logits, _ = model(conditioned)
            step_logits = logits[:, -1, :]
            if temperature <= 0.0:
                next_id = torch.argmax(step_logits, dim=-1, keepdim=True)
            else:
                step_logits = step_logits / temperature
                if top_k is not None:
                    step_logits = _apply_top_k(step_logits, top_k)
                probs = F.softmax(step_logits, dim=-1)
                if generator is not None:
                    next_id = torch.multinomial(probs.cpu(), 1, generator=generator).to(dev)
                else:
                    next_id = torch.multinomial(probs, 1)
            idx = torch.cat([idx, next_id], dim=1)

    new_ids = idx[0, len(ids) :].tolist()
    return tok.decode(new_ids)
