"""Interactive chat client for `sovereign-agent chat` (v0.3, Module 1).

`sovereign-agent chat` gives a student their first real conversation with
an agent they built. It is deliberately small and stdlib-only — no curses,
no readline wrappers, just asyncio Unix-socket I/O and stdin.

## Server-or-client

If a CLI channel socket is already being served — e.g. by a separate
`sovereign-agent serve` process — `chat` simply connects to it as a client.
If nothing is listening, `chat` starts an *embedded* orchestrator with a
`CliChannelAdapter`, waits for the socket to come up, then connects to its
own adapter. Either way the student types into a REPL and the agent
answers; the difference between the two modes is exactly the lesson of
Chapter 6 (transport is separable from behaviour).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys
from pathlib import Path

from sovereign_agent.config import Config


async def _connect(socket_path: Path) -> tuple | None:
    """Try to connect to an existing CLI channel socket.

    Returns (reader, writer) on success, or None if nothing is listening.
    """
    try:
        return await asyncio.open_unix_connection(path=str(socket_path))
    except (FileNotFoundError, ConnectionRefusedError, OSError):
        return None


async def _reader_loop(reader: asyncio.StreamReader) -> None:
    """Print every agent reply as it arrives."""
    while True:
        line = await reader.readline()
        if not line:
            print("\n[connection closed]")
            return
        try:
            obj = json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        print(f"\nagent> {obj.get('text', '')}\n> ", end="", flush=True)


async def _stdin_loop(writer: asyncio.StreamWriter) -> None:
    """Read lines from stdin and send each as a JSON message."""
    loop = asyncio.get_event_loop()
    print("> ", end="", flush=True)
    while True:
        # stdin.readline is blocking; run it off the event loop.
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:  # EOF (Ctrl-D)
            return
        text = line.strip()
        if not text:
            print("> ", end="", flush=True)
            continue
        writer.write((json.dumps({"text": text}) + "\n").encode("utf-8"))
        await writer.drain()


async def _chat_against(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    reader_task = asyncio.create_task(_reader_loop(reader))
    stdin_task = asyncio.create_task(_stdin_loop(writer))
    _, pending = await asyncio.wait({reader_task, stdin_task}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def run_chat(config: Config, *, socket_path: Path) -> None:
    """Entry point for the `chat` subcommand. Blocks until the user exits."""

    async def _main() -> None:
        conn = await _connect(socket_path)
        orchestrator = None
        orch_task = None
        if conn is None:
            # Nothing listening — start an embedded orchestrator with a CLI
            # channel adapter, then connect to its socket.
            from sovereign_agent.channels.cli import CliChannelAdapter
            from sovereign_agent.orchestrator import Orchestrator

            orchestrator = Orchestrator(
                config, adapters=[CliChannelAdapter(socket_path=socket_path)]
            )
            orch_task = asyncio.create_task(orchestrator.run())
            for _ in range(100):  # up to ~5s for the socket to appear
                await asyncio.sleep(0.05)
                conn = await _connect(socket_path)
                if conn is not None:
                    break
            if conn is None:
                orch_task.cancel()
                raise RuntimeError("CLI channel socket did not come up")

        reader, writer = conn
        print(f"connected to {socket_path}. Type a message; Ctrl-C or Ctrl-D to exit.")
        try:
            await _chat_against(reader, writer)
        finally:
            with contextlib.suppress(Exception):
                writer.close()
            if orchestrator is not None:
                await orchestrator.shutdown()
            if orch_task is not None:
                orch_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await orch_task

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print("\nbye")


__all__ = ["run_chat"]
