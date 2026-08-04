"""CLI tests for --version, --help and doctor."""

from __future__ import annotations

import pytest

from aira import __version__
from aira.cli.main import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_args_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    code = main([])
    assert code == 0
    out = capsys.readouterr().out
    assert "usage: aira" in out
    assert "doctor" in out


def test_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "usage: aira" in capsys.readouterr().out


def test_doctor_runs(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["doctor"])
    assert code == 0
    out = capsys.readouterr().out
    assert f"Aira LM {__version__}" in out
    assert "Selected device" in out
    assert "Config" in out


def test_doctor_reports_config_ok(capsys: pytest.CaptureFixture[str]) -> None:
    # Run from the repo root, where configs/aira_tiny.toml exists.
    code = main(["doctor"])
    assert code == 0
    assert "Config           OK" in capsys.readouterr().out
