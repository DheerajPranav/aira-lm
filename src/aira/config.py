"""Configuration loading and validation for Aira LM.

Parses ``configs/aira_tiny.toml`` with the standard-library ``tomllib`` into typed,
frozen dataclasses and validates ranges and invariants up front. Loading is the only
place configuration values are trusted; every consumer receives an already-validated
:class:`AiraConfig`.

No third-party dependency is used here.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("configs/aira_tiny.toml")

_VALID_RETRIEVAL_BACKENDS = frozenset({"auto", "fts5", "bm25"})


class ConfigError(ValueError):
    """Raised when a configuration file is missing required data or is out of range."""


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Project identity."""

    name: str
    tagline: str


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Aira Core model shape. Not instantiated as a model until Step 11."""

    vocab_size: int
    context_length: int
    embedding_dim: int
    layers: int
    heads: int
    ffn_multiplier: int
    dropout: float
    tie_embeddings: bool


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """Decoding defaults."""

    max_new_tokens: int
    temperature: float
    top_k: int


@dataclass(frozen=True, slots=True)
class MemoryConfig:
    """Memory-runtime limits and defaults."""

    default_owner_id: str
    max_record_bytes: int
    context_token_budget: int
    top_k: int


@dataclass(frozen=True, slots=True)
class RetrievalConfig:
    """Retrieval backend selection and ranking weights."""

    backend: str
    lexical_weight: float
    importance_weight: float
    confidence_weight: float
    recency_weight: float
    reinforcement_weight: float
    project_weight: float
    kind_weight: float
    decay_penalty_weight: float


@dataclass(frozen=True, slots=True)
class DecayConfig:
    """Aira Fade decay/archival parameters."""

    enabled: bool
    archive_threshold: float
    episodic_half_life_days: float
    semantic_half_life_days: float
    preference_half_life_days: float
    instruction_half_life_days: float


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Process-level runtime settings."""

    seed: int
    database_path: str
    offline: bool
    debug: bool


@dataclass(frozen=True, slots=True)
class AiraConfig:
    """The complete, validated configuration for one Aira LM process."""

    project: ProjectConfig
    model: ModelConfig
    generation: GenerationConfig
    memory: MemoryConfig
    retrieval: RetrievalConfig
    decay: DecayConfig
    runtime: RuntimeConfig


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> AiraConfig:
    """Load and validate an Aira configuration file.

    Args:
        path: Path to a TOML configuration file.

    Returns:
        A validated :class:`AiraConfig`.

    Raises:
        ConfigError: If the file is missing, unparseable, missing a required
            section or key, has a wrong type, or holds an out-of-range value.
    """
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"configuration file not found: {p}")
    try:
        raw = tomllib.loads(p.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise ConfigError(f"could not read configuration {p}: {exc}") from exc
    return _build_config(raw)


def _section(raw: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = raw.get(name)
    if not isinstance(value, Mapping):
        raise ConfigError(f"missing or invalid [{name}] section")
    return value


def _req(section: Mapping[str, Any], sect_name: str, key: str, expected: type) -> Any:
    if key not in section:
        raise ConfigError(f"[{sect_name}] is missing required key '{key}'")
    value = section[key]
    # bool is a subclass of int; guard against silently accepting True as an int.
    if expected is int and isinstance(value, bool):
        raise ConfigError(f"[{sect_name}].{key} must be an integer, not a boolean")
    if expected is float and isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, expected):
        raise ConfigError(
            f"[{sect_name}].{key} must be {expected.__name__}, got {type(value).__name__}"
        )
    return value


def _positive(name: str, value: float) -> float:
    if value <= 0:
        raise ConfigError(f"{name} must be > 0, got {value}")
    return value


def _unit(name: str, value: float) -> float:
    if not 0.0 <= value <= 1.0:
        raise ConfigError(f"{name} must be within [0, 1], got {value}")
    return value


def _build_config(raw: Mapping[str, Any]) -> AiraConfig:
    proj = _section(raw, "project")
    project = ProjectConfig(
        name=_req(proj, "project", "name", str),
        tagline=_req(proj, "project", "tagline", str),
    )

    m = _section(raw, "model")
    model = ModelConfig(
        vocab_size=int(_positive("[model].vocab_size", _req(m, "model", "vocab_size", int))),
        context_length=int(
            _positive("[model].context_length", _req(m, "model", "context_length", int))
        ),
        embedding_dim=int(
            _positive("[model].embedding_dim", _req(m, "model", "embedding_dim", int))
        ),
        layers=int(_positive("[model].layers", _req(m, "model", "layers", int))),
        heads=int(_positive("[model].heads", _req(m, "model", "heads", int))),
        ffn_multiplier=int(
            _positive("[model].ffn_multiplier", _req(m, "model", "ffn_multiplier", int))
        ),
        dropout=_req(m, "model", "dropout", float),
        tie_embeddings=_req(m, "model", "tie_embeddings", bool),
    )
    if not 0.0 <= model.dropout < 1.0:
        raise ConfigError(f"[model].dropout must be within [0, 1), got {model.dropout}")
    if model.embedding_dim % model.heads != 0:
        raise ConfigError(
            f"[model].embedding_dim ({model.embedding_dim}) must be divisible by "
            f"[model].heads ({model.heads})"
        )

    g = _section(raw, "generation")
    generation = GenerationConfig(
        max_new_tokens=int(
            _positive("[generation].max_new_tokens", _req(g, "generation", "max_new_tokens", int))
        ),
        temperature=_positive(
            "[generation].temperature", _req(g, "generation", "temperature", float)
        ),
        top_k=_req(g, "generation", "top_k", int),
    )
    if generation.top_k < 0:
        raise ConfigError(f"[generation].top_k must be >= 0, got {generation.top_k}")

    mem = _section(raw, "memory")
    memory = MemoryConfig(
        default_owner_id=_req(mem, "memory", "default_owner_id", str),
        max_record_bytes=int(
            _positive("[memory].max_record_bytes", _req(mem, "memory", "max_record_bytes", int))
        ),
        context_token_budget=int(
            _positive(
                "[memory].context_token_budget",
                _req(mem, "memory", "context_token_budget", int),
            )
        ),
        top_k=int(_positive("[memory].top_k", _req(mem, "memory", "top_k", int))),
    )
    if not memory.default_owner_id.strip():
        raise ConfigError("[memory].default_owner_id must not be empty")

    r = _section(raw, "retrieval")
    backend = _req(r, "retrieval", "backend", str)
    if backend not in _VALID_RETRIEVAL_BACKENDS:
        allowed = sorted(_VALID_RETRIEVAL_BACKENDS)
        raise ConfigError(f"[retrieval].backend must be one of {allowed}, got '{backend}'")
    retrieval = RetrievalConfig(
        backend=backend,
        lexical_weight=_unit(
            "[retrieval].lexical_weight", _req(r, "retrieval", "lexical_weight", float)
        ),
        importance_weight=_unit(
            "[retrieval].importance_weight", _req(r, "retrieval", "importance_weight", float)
        ),
        confidence_weight=_unit(
            "[retrieval].confidence_weight", _req(r, "retrieval", "confidence_weight", float)
        ),
        recency_weight=_unit(
            "[retrieval].recency_weight", _req(r, "retrieval", "recency_weight", float)
        ),
        reinforcement_weight=_unit(
            "[retrieval].reinforcement_weight", _req(r, "retrieval", "reinforcement_weight", float)
        ),
        project_weight=_unit(
            "[retrieval].project_weight", _req(r, "retrieval", "project_weight", float)
        ),
        kind_weight=_unit("[retrieval].kind_weight", _req(r, "retrieval", "kind_weight", float)),
        decay_penalty_weight=_unit(
            "[retrieval].decay_penalty_weight", _req(r, "retrieval", "decay_penalty_weight", float)
        ),
    )

    d = _section(raw, "decay")
    decay = DecayConfig(
        enabled=_req(d, "decay", "enabled", bool),
        archive_threshold=_unit(
            "[decay].archive_threshold", _req(d, "decay", "archive_threshold", float)
        ),
        episodic_half_life_days=_positive(
            "[decay].episodic_half_life_days", _req(d, "decay", "episodic_half_life_days", float)
        ),
        semantic_half_life_days=_positive(
            "[decay].semantic_half_life_days", _req(d, "decay", "semantic_half_life_days", float)
        ),
        preference_half_life_days=_positive(
            "[decay].preference_half_life_days",
            _req(d, "decay", "preference_half_life_days", float),
        ),
        instruction_half_life_days=_positive(
            "[decay].instruction_half_life_days",
            _req(d, "decay", "instruction_half_life_days", float),
        ),
    )

    rt = _section(raw, "runtime")
    runtime = RuntimeConfig(
        seed=_req(rt, "runtime", "seed", int),
        database_path=_req(rt, "runtime", "database_path", str),
        offline=_req(rt, "runtime", "offline", bool),
        debug=_req(rt, "runtime", "debug", bool),
    )
    if runtime.seed < 0:
        raise ConfigError(f"[runtime].seed must be >= 0, got {runtime.seed}")
    if not runtime.database_path.strip():
        raise ConfigError("[runtime].database_path must not be empty")

    return AiraConfig(
        project=project,
        model=model,
        generation=generation,
        memory=memory,
        retrieval=retrieval,
        decay=decay,
        runtime=runtime,
    )
