"""A compact decoder-only causal transformer (Aira Core), written directly in PyTorch.

Standard, readable GPT-style architecture: learned token + positional embeddings, pre-norm
blocks with multi-head causal self-attention and a GELU feed-forward, a final norm and a
(optionally tied) language-model head. No pretrained weights, no architectural novelty.
The default configuration lands near 5–10M parameters and is safe on an M2.
"""

from __future__ import annotations

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from aira.config import ModelConfig


class CausalSelfAttention(nn.Module):
    """Multi-head self-attention with an explicit causal mask (no future tokens)."""

    def __init__(self, dim: int, heads: int, dropout: float) -> None:
        super().__init__()
        if dim % heads != 0:
            raise ValueError(f"embedding_dim ({dim}) must be divisible by heads ({heads})")
        self.heads = heads
        self.head_dim = dim // heads
        self.scale = self.head_dim**-0.5
        self.qkv = nn.Linear(dim, 3 * dim)
        self.proj = nn.Linear(dim, dim)
        self.attn_drop = nn.Dropout(dropout)
        self.resid_drop = nn.Dropout(dropout)

    def forward(self, x: Tensor) -> Tensor:
        """Attend over ``x`` of shape (batch, seq, dim), masking future positions."""
        batch, seq, dim = x.shape
        q, k, v = self.qkv(x).split(dim, dim=2)
        q = q.view(batch, seq, self.heads, self.head_dim).transpose(1, 2)
        k = k.view(batch, seq, self.heads, self.head_dim).transpose(1, 2)
        v = v.view(batch, seq, self.heads, self.head_dim).transpose(1, 2)

        att = (q @ k.transpose(-2, -1)) * self.scale  # (batch, heads, seq, seq)
        causal = torch.tril(torch.ones(seq, seq, device=x.device, dtype=torch.bool))
        att = att.masked_fill(~causal, float("-inf"))
        att = self.attn_drop(torch.softmax(att, dim=-1))

        y = att @ v  # (batch, heads, seq, head_dim)
        y = y.transpose(1, 2).contiguous().view(batch, seq, dim)
        out: Tensor = self.resid_drop(self.proj(y))
        return out


class FeedForward(nn.Module):
    """Position-wise GELU feed-forward network."""

    def __init__(self, dim: int, multiplier: int, dropout: float) -> None:
        super().__init__()
        self.fc1 = nn.Linear(dim, multiplier * dim)
        self.fc2 = nn.Linear(multiplier * dim, dim)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: Tensor) -> Tensor:
        """Apply the two-layer GELU MLP."""
        out: Tensor = self.drop(self.fc2(F.gelu(self.fc1(x))))
        return out


class Block(nn.Module):
    """A pre-norm transformer block: x + attn(norm(x)), then x + ffn(norm(x))."""

    def __init__(self, dim: int, heads: int, multiplier: int, dropout: float) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(dim)
        self.attn = CausalSelfAttention(dim, heads, dropout)
        self.ln2 = nn.LayerNorm(dim)
        self.ffn = FeedForward(dim, multiplier, dropout)

    def forward(self, x: Tensor) -> Tensor:
        """Run attention and feed-forward with residual connections."""
        x = x + self.attn(self.ln1(x))
        out: Tensor = x + self.ffn(self.ln2(x))
        return out


class AiraCore(nn.Module):
    """A tiny decoder-only causal language model."""

    def __init__(
        self,
        *,
        vocab_size: int,
        context_length: int,
        embedding_dim: int,
        layers: int,
        heads: int,
        ffn_multiplier: int,
        dropout: float,
        tie_embeddings: bool,
    ) -> None:
        super().__init__()
        self.context_length = context_length
        self.vocab_size = vocab_size
        self.token_embedding = nn.Embedding(vocab_size, embedding_dim)
        self.position_embedding = nn.Embedding(context_length, embedding_dim)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList(
            Block(embedding_dim, heads, ffn_multiplier, dropout) for _ in range(layers)
        )
        self.ln_f = nn.LayerNorm(embedding_dim)
        self.lm_head = nn.Linear(embedding_dim, vocab_size, bias=False)
        if tie_embeddings:
            self.lm_head.weight = self.token_embedding.weight
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx: Tensor, targets: Tensor | None = None) -> tuple[Tensor, Tensor | None]:
        """Return (logits, loss). ``loss`` is the causal cross-entropy when targets are given."""
        _batch, seq = idx.shape
        if seq > self.context_length:
            raise ValueError(f"sequence length {seq} exceeds context {self.context_length}")
        positions = torch.arange(seq, device=idx.device)
        x = self.token_embedding(idx) + self.position_embedding(positions)
        x = self.drop(x)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        logits: Tensor = self.lm_head(x)  # (batch, seq, vocab)

        loss: Tensor | None = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    def parameter_count(self) -> int:
        """Return the exact number of parameters (tied weights counted once)."""
        return sum(p.numel() for p in self.parameters())

    def greedy_generate(self, idx: Tensor, max_new_tokens: int) -> Tensor:
        """Deterministically extend ``idx`` by greedy (argmax) decoding.

        Temperature and top-k sampling arrive in Step 12; this is the minimal decoding the
        backend needs.
        """
        was_training = self.training
        self.eval()
        with torch.no_grad():
            for _ in range(max_new_tokens):
                conditioned = idx[:, -self.context_length :]
                logits, _ = self.forward(conditioned)
                next_id = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
                idx = torch.cat([idx, next_id], dim=1)
        if was_training:
            self.train()
        return idx


def from_config(cfg: ModelConfig) -> AiraCore:
    """Build an :class:`AiraCore` from the ``[model]`` configuration section."""
    return AiraCore(
        vocab_size=cfg.vocab_size,
        context_length=cfg.context_length,
        embedding_dim=cfg.embedding_dim,
        layers=cfg.layers,
        heads=cfg.heads,
        ffn_multiplier=cfg.ffn_multiplier,
        dropout=cfg.dropout,
        tie_embeddings=cfg.tie_embeddings,
    )


def build_model(cfg: ModelConfig, *, seed: int | None = None) -> AiraCore:
    """Build a model, optionally seeding torch first for deterministic initialization."""
    if seed is not None:
        torch.manual_seed(seed)
    return from_config(cfg)


__all__ = [
    "AiraCore",
    "Block",
    "CausalSelfAttention",
    "FeedForward",
    "build_model",
    "from_config",
]
