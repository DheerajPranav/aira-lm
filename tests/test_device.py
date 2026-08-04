"""Device-selection tests using fake torch modules (no real PyTorch required)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from aira import device


def _fake_torch(*, mps: bool, cuda: bool, version: str = "9.9.9") -> SimpleNamespace:
    return SimpleNamespace(
        __version__=version,
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: mps)),
        cuda=SimpleNamespace(is_available=lambda: cuda),
    )


def test_no_torch_selects_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: None)
    assert device.select_device() == "cpu"
    assert device.available_devices() == {"mps": False, "cuda": False, "cpu": True}


def test_mps_preferred(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: _fake_torch(mps=True, cuda=True))
    assert device.select_device() == "mps"


def test_cuda_when_no_mps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: _fake_torch(mps=False, cuda=True))
    assert device.select_device() == "cuda"


def test_prefer_available_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: _fake_torch(mps=True, cuda=True))
    assert device.select_device(prefer="cuda") == "cuda"


def test_prefer_unavailable_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: _fake_torch(mps=True, cuda=False))
    # prefer cuda but it's unavailable -> falls back to normal order (mps)
    assert device.select_device(prefer="cuda") == "mps"


def test_prefer_unknown_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: None)
    with pytest.raises(ValueError, match="unknown device"):
        device.select_device(prefer="tpu")


def test_describe_devices_no_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: None)
    info = device.describe_devices()
    assert info["torch_installed"] is False
    assert info["selected"] == "cpu"


def test_describe_devices_with_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "_import_torch", lambda: _fake_torch(mps=True, cuda=False))
    info = device.describe_devices()
    assert info["torch_installed"] is True
    assert info["torch_version"] == "9.9.9"
    assert info["selected"] == "mps"
