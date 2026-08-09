"""Entry point for the ``aira`` command-line interface.

Provides ``aira --version``, ``aira --help`` and ``aira doctor``. ``doctor`` prints a
diagnostic report — interpreter version (warning when it is not the 3.12 target),
platform, device availability and whether the default configuration loads — without
requiring any optional dependency.
"""

from __future__ import annotations

import argparse
import platform
import sys
from collections.abc import Sequence
from io import StringIO

from aira import __version__
from aira.config import DEFAULT_CONFIG_PATH, ConfigError, load_config
from aira.device import describe_devices

# Chat wiring is imported lazily inside the command to keep `aira doctor`/`--version`
# free of heavier memory-runtime imports.

_TARGET_PYTHON = (3, 12)


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="aira",
        description="Aira LM — small model, long memory, gentle by design.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"aira {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")
    doctor = subparsers.add_parser(
        "doctor",
        help="Report environment, devices and configuration status.",
    )
    doctor.set_defaults(func=_cmd_doctor)

    chat = subparsers.add_parser(
        "chat",
        help="Interactive memory chat over the deterministic mock backend.",
    )
    chat.add_argument("--owner", default=None, help="Owner id (defaults to config value).")
    chat.set_defaults(func=_cmd_chat)

    fade = subparsers.add_parser(
        "fade",
        help="Run the decay/expiry/archival job once (never hard-deletes).",
    )
    fade.add_argument("--owner", default=None, help="Restrict to one owner (default: all).")
    fade.set_defaults(func=_cmd_fade)
    return parser


def _cmd_chat(args: argparse.Namespace) -> int:
    """Start an interactive memory chat over the mock backend. Returns an exit code."""
    from aira.chat import create_chat_engine, run_session
    from aira.memory.vault import connect

    cfg = load_config(DEFAULT_CONFIG_PATH)
    owner = args.owner or cfg.memory.default_owner_id
    connection = connect(cfg.runtime.database_path)
    engine = create_chat_engine(cfg, connection)

    sys.stdout.write(
        "Aira chat (deterministic mock backend — not a trained model).\n"
        "Type a message, or a command. /exit to quit.\n"
    )
    run_session(engine, owner, sys.stdin, sys.stdout)
    return 0


def _cmd_fade(args: argparse.Namespace) -> int:
    """Run the fade job once over the configured database. Returns an exit code."""
    from aira.chat import create_chat_engine
    from aira.memory.vault import connect

    cfg = load_config(DEFAULT_CONFIG_PATH)
    engine = create_chat_engine(cfg, connect(cfg.runtime.database_path))
    report = engine.run_fade(owner_id=args.owner)
    sys.stdout.write(
        f"Aira Fade: scanned={report.scanned} archived={report.archived_count} "
        f"expired={report.expired_count}\n"
    )
    return 0


def _cmd_doctor(_args: argparse.Namespace, out: StringIO | None = None) -> int:
    """Print an environment diagnostic. Returns a process exit code."""
    stream = out if out is not None else sys.stdout
    lines: list[str] = []
    lines.append(f"Aira LM {__version__}")
    lines.append("=" * 32)

    py = sys.version_info
    py_str = f"{py.major}.{py.minor}.{py.micro}"
    if (py.major, py.minor) == _TARGET_PYTHON:
        lines.append(f"Python           {py_str} (target)")
    else:
        target = ".".join(str(n) for n in _TARGET_PYTHON)
        lines.append(f"Python           {py_str}  WARNING: target is {target}")

    lines.append(f"Platform         {platform.platform()}")
    lines.append(f"Machine          {platform.machine()}")

    devices = describe_devices()
    available = devices["available"]
    assert isinstance(available, dict)
    ready = ", ".join(name for name, ok in available.items() if ok)
    lines.append(f"Torch installed  {devices['torch_installed']}")
    lines.append(f"Devices ready    {ready}")
    lines.append(f"Selected device  {devices['selected']}")

    try:
        cfg = load_config(DEFAULT_CONFIG_PATH)
        lines.append(f"Config           OK  ({DEFAULT_CONFIG_PATH})")
        lines.append(f"  project        {cfg.project.name}")
        lines.append(f"  offline        {cfg.runtime.offline}")
        lines.append(f"  seed           {cfg.runtime.seed}")
    except ConfigError as exc:
        lines.append(f"Config           NOT LOADED ({DEFAULT_CONFIG_PATH}): {exc}")

    stream.write("\n".join(lines) + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``aira`` CLI.

    Args:
        argv: Argument vector excluding the program name. Defaults to ``sys.argv[1:]``.

    Returns:
        A process exit code. Running with no command prints help and returns 0.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    exit_code = func(args)
    return int(exit_code)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
