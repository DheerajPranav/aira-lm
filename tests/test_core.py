"""Tests for Aira Core: byte tokenizer, transformer correctness, and the backend."""

from __future__ import annotations

import pytest
import torch

from aira.chat.backend import GenerationBackend, GenerationRequest
from aira.config import load_config
from aira.core import AiraCore, ByteTokenizer, TinyTransformerBackend, build_model
from aira.device import select_device

_CFG = load_config("configs/aira_tiny.toml")


@pytest.fixture(scope="module")
def model() -> AiraCore:
    return build_model(_CFG.model, seed=42).eval()


# --- tokenizer ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["hello world", "café déjà vu ☕✨", "punct!? — (yes/no) [x]", "", "vim\nfish\t3.2"],
)
def test_tokenizer_round_trip(text: str) -> None:
    tok = ByteTokenizer()
    assert tok.decode(tok.encode(text)) == text


def test_tokenizer_vocab_and_count() -> None:
    tok = ByteTokenizer()
    assert tok.vocab_size == 256
    assert tok.count("café") == len("café".encode())


def test_tokenizer_invalid_bytes_do_not_raise() -> None:
    tok = ByteTokenizer()
    # 0xFF/0xFE are not valid standalone UTF-8; decode replaces rather than raising.
    assert isinstance(tok.decode([255, 254, 200]), str)


def test_tokenizer_rejects_out_of_range_id() -> None:
    with pytest.raises(ValueError, match="byte range"):
        ByteTokenizer().decode([256])


# --- model correctness -------------------------------------------------------------


def test_output_shape(model: AiraCore) -> None:
    idx = torch.randint(0, 256, (2, 16))
    logits, loss = model(idx)
    assert logits.shape == (2, 16, 256)
    assert loss is None


def test_loss_is_finite(model: AiraCore) -> None:
    idx = torch.randint(0, 256, (2, 16))
    _, loss = model(idx, idx)
    assert loss is not None
    assert torch.isfinite(loss)
    assert loss.item() > 0


def test_no_future_token_influence(model: AiraCore) -> None:
    idx = torch.randint(0, 256, (1, 8))
    changed = idx.clone()
    changed[0, -1] = (idx[0, -1] + 1) % 256  # change only the last token
    with torch.no_grad():
        base, _ = model(idx)
        alt, _ = model(changed)
    # positions before the changed token must be identical (no leakage from the future)
    assert torch.allclose(base[0, :-1], alt[0, :-1], atol=1e-6)


def test_parameter_count_in_range(model: AiraCore) -> None:
    count = model.parameter_count()
    assert 5_000_000 <= count <= 10_000_000


def test_context_length_enforced(model: AiraCore) -> None:
    too_long = torch.zeros((1, _CFG.model.context_length + 1), dtype=torch.long)
    with pytest.raises(ValueError, match="exceeds context"):
        model(too_long)


# --- determinism -------------------------------------------------------------------


def test_deterministic_initialization() -> None:
    a = build_model(_CFG.model, seed=7)
    b = build_model(_CFG.model, seed=7)
    assert torch.equal(a.token_embedding.weight, b.token_embedding.weight)
    assert torch.equal(a.lm_head.weight, b.lm_head.weight)


def test_embeddings_are_tied() -> None:
    m = build_model(_CFG.model, seed=1)
    assert m.lm_head.weight is m.token_embedding.weight  # tie_embeddings = true


def test_greedy_generation_is_deterministic(model: AiraCore) -> None:
    idx = torch.tensor([[1, 2, 3, 4]])
    out1 = model.greedy_generate(idx, 6)
    out2 = model.greedy_generate(idx, 6)
    assert torch.equal(out1, out2)
    assert out1.shape == (1, 10)


# --- device smoke ------------------------------------------------------------------


def test_forward_on_selected_device() -> None:
    device = select_device()  # mps on M2, else cpu
    m = build_model(_CFG.model, seed=0).eval().to(device)
    idx = torch.zeros((1, 8), dtype=torch.long, device=device)
    with torch.no_grad():
        logits, _ = m(idx)
    assert logits.shape == (1, 8, 256)


def test_forward_on_cpu() -> None:
    m = build_model(_CFG.model, seed=0).eval().to("cpu")
    idx = torch.zeros((1, 8), dtype=torch.long)
    with torch.no_grad():
        logits, _ = m(idx)
    assert logits.shape == (1, 8, 256)


# --- backend adapter ---------------------------------------------------------------


def test_backend_satisfies_protocol(model: AiraCore) -> None:
    backend = TinyTransformerBackend(model, device="cpu", max_new_tokens=8)
    assert isinstance(backend, GenerationBackend)


def test_backend_generates_deterministically() -> None:
    model = build_model(_CFG.model, seed=3)
    backend = TinyTransformerBackend(model, device="cpu", max_new_tokens=8)
    request = GenerationRequest(message="hello", memory_context="")
    first = backend.generate(request)
    second = backend.generate(request)
    assert isinstance(first, str)
    assert first == second  # greedy decoding is deterministic
