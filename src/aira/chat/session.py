"""Interactive chat session: slash commands over a :class:`ChatEngine`.

Kept as a pure function over an input iterable and an output stream so it is fully
testable without real stdin/stdout. The CLI wires real streams to it. Internal memory
ids are shown only when debug mode is on.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import TextIO

from aira.chat.engine import ChatEngine
from aira.chat.models import SessionStats
from aira.memory.domain.clock import utc_now

_HELP = "Commands: /memories  /memory <id>  /forget <id>  /debug  /stats  /reset  /exit"


def run_session(
    engine: ChatEngine,
    owner_id: str,
    lines: Iterable[str],
    out: TextIO,
    *,
    now_factory: Callable[[], datetime] = utc_now,
) -> SessionStats:
    """Drive a chat session from ``lines``, writing responses to ``out``.

    Returns the session stats. A ``/exit`` line (or exhausting ``lines``) ends the session.
    """
    stats = SessionStats()
    debug = False

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("/"):
            command, _, arg = line[1:].partition(" ")
            arg = arg.strip()
            if command == "exit":
                break
            debug = _handle_command(engine, owner_id, command, arg, out, stats, debug, now_factory)
            continue

        response = engine.chat(owner_id, line, now=now_factory(), debug=debug)
        stats.record(response)
        out.write(response.text + "\n")
        if debug and response.debug is not None:
            out.write(
                f"[correlation={response.correlation_id} latency={response.latency_ms}ms "
                f"memory_used={response.memory_used} degraded={response.degraded}]\n"
            )
    return stats


def _handle_command(
    engine: ChatEngine,
    owner_id: str,
    command: str,
    arg: str,
    out: TextIO,
    stats: SessionStats,
    debug: bool,
    now_factory: Callable[[], datetime],
) -> bool:
    """Handle one slash command. Returns the (possibly toggled) debug flag."""
    if command == "debug":
        debug = not debug
        out.write(f"debug {'on' if debug else 'off'}\n")
    elif command == "memories":
        _list_memories(engine, owner_id, out, debug)
    elif command == "memory":
        _show_memory(engine, owner_id, arg, out, debug)
    elif command == "forget":
        ok = engine.forget(owner_id, arg, now=now_factory()) if arg else False
        out.write("forgotten\n" if ok else "no such memory\n")
    elif command == "stats":
        out.write(
            f"messages={stats.messages} memory_used={stats.memory_used} "
            f"degraded={stats.degraded} avg_latency_ms={stats.average_latency_ms}\n"
        )
    elif command == "reset":
        stats.messages = 0
        stats.memory_used = 0
        stats.degraded = 0
        stats.total_latency_ms = 0.0
        out.write("session stats reset (stored memories are unchanged)\n")
    else:
        out.write(_HELP + "\n")
    return debug


def _list_memories(engine: ChatEngine, owner_id: str, out: TextIO, debug: bool) -> None:
    records = engine.memories(owner_id)
    if not records:
        out.write("(no memories)\n")
        return
    for i, record in enumerate(records, start=1):
        prefix = f"{record.id} " if debug else ""
        out.write(f"[{i}] {prefix}({record.kind.value}) {record.content}\n")


def _show_memory(
    engine: ChatEngine, owner_id: str, memory_id: str, out: TextIO, debug: bool
) -> None:
    if not memory_id:
        out.write("usage: /memory <id>\n")
        return
    for record in engine.memories(owner_id):
        if record.id == memory_id:
            extra = f" source={record.provenance.source.value}" if debug else ""
            out.write(f"({record.kind.value}) {record.content}{extra}\n")
            return
    out.write("no such memory\n")
