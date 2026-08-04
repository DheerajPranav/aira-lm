"""Compute-device selection: MPS, then CUDA, then CPU.

PyTorch is an optional dependency (the ``core`` extra, installed at Step 11), so it is
imported lazily. When torch is unavailable the selected device is always ``"cpu"`` and
:func:`describe_devices` reports it as absent. The lazy import lives in
:func:`_import_torch` so tests can substitute a fake torch module.
"""

from __future__ import annotations

from types import ModuleType

Device = str  # one of: "mps", "cuda", "cpu"

_PREFERENCE_ORDER: tuple[Device, ...] = ("mps", "cuda", "cpu")


def _import_torch() -> ModuleType | None:
    """Return the ``torch`` module if installed, else ``None``.

    Isolated here so tests can monkeypatch device availability without installing
    PyTorch.
    """
    try:
        import torch
    except ImportError:
        return None
    module: ModuleType = torch
    return module


def _mps_available(torch: ModuleType) -> bool:
    backends = getattr(torch, "backends", None)
    mps = getattr(backends, "mps", None) if backends is not None else None
    is_available = getattr(mps, "is_available", None) if mps is not None else None
    return bool(is_available()) if callable(is_available) else False


def _cuda_available(torch: ModuleType) -> bool:
    cuda = getattr(torch, "cuda", None)
    is_available = getattr(cuda, "is_available", None) if cuda is not None else None
    return bool(is_available()) if callable(is_available) else False


def available_devices() -> dict[Device, bool]:
    """Report which devices are usable right now.

    Returns:
        A mapping of device name to availability. ``"cpu"`` is always ``True``;
        ``"mps"`` and ``"cuda"`` are ``False`` when PyTorch is not installed.
    """
    torch = _import_torch()
    if torch is None:
        return {"mps": False, "cuda": False, "cpu": True}
    return {
        "mps": _mps_available(torch),
        "cuda": _cuda_available(torch),
        "cpu": True,
    }


def select_device(prefer: Device | None = None) -> Device:
    """Select the best available compute device.

    The order is MPS, then CUDA, then CPU. If ``prefer`` is given and available, it
    wins; if ``prefer`` is given but unavailable, selection falls back to the normal
    order rather than raising, so callers always get a usable device.

    Args:
        prefer: An optional device to prefer (``"mps"``, ``"cuda"`` or ``"cpu"``).

    Returns:
        The name of a usable device. Always ``"cpu"`` when PyTorch is absent.

    Raises:
        ValueError: If ``prefer`` is not a recognized device name.
    """
    if prefer is not None and prefer not in _PREFERENCE_ORDER:
        raise ValueError(f"unknown device '{prefer}', expected one of {list(_PREFERENCE_ORDER)}")

    available = available_devices()
    if prefer is not None and available.get(prefer, False):
        return prefer
    for device in _PREFERENCE_ORDER:
        if available.get(device, False):
            return device
    return "cpu"


def describe_devices() -> dict[str, object]:
    """Return a human/diagnostic-friendly device summary for ``aira doctor``."""
    torch = _import_torch()
    available = available_devices()
    return {
        "torch_installed": torch is not None,
        "torch_version": getattr(torch, "__version__", None),
        "available": available,
        "selected": select_device(),
    }
