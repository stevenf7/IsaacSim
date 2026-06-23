# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base agent-session machinery shared by every backend.

Spawns one agent subprocess per conversational turn, reads its stdout on a
daemon thread, and forwards parsed events to a caller-supplied callback. Wire
parsing is delegated to an injected :class:`~.stream_events.ResponseParser`, so
concrete backends differ only in their CLI flags (see :meth:`AgentSession._build_argv`).
"""

from __future__ import annotations

import abc
import os
import subprocess
import threading
from collections.abc import Callable

from .stream_events import ErrorEvent, InitEvent, ResponseParser, ResultEvent, StreamEvent

# Relative to the repo root — the in-repo socket client the agent shells out to.
SCRIPTS_RELPATH = os.path.join("skills", "isaac-sim-remote", "scripts")


class AgentSession(abc.ABC):
    """Spawn and read one agent subprocess per conversational turn.

    The base owns the per-turn subprocess lifecycle (spawn, reader thread,
    parse, session-id capture, stop) and delegates wire parsing to the injected
    parser. Concrete backends implement :meth:`_build_argv` to supply their own
    launch flags.

    Args:
        repo_root: Working directory for the agent subprocess; its repo-relative
            paths (skills, socket scripts) resolve against this.
        port: The python_server loopback port handed to the agent.
        agent_path: Path to (or name of) the agent executable to launch.
        system_prompt: Full system-prompt override; falls back to a built-in
            default when ``None``.
        system_prompt_append: Extra text appended to the system prompt (the
            built-in default or the ``system_prompt`` override). Empty to append
            nothing. Lets a user extend the agent's instructions via settings.
        parser: Backend parser mapping the agent's wire output to typed events.
    """

    def __init__(
        self,
        repo_root: str,
        port: int,
        agent_path: str,
        system_prompt: str | None = None,
        system_prompt_append: str = "",
        parser: ResponseParser | None = None,
    ) -> None:
        self._repo_root = repo_root
        self._port = port
        self._argv0 = [agent_path]
        self._scripts_dir = os.path.join(repo_root, SCRIPTS_RELPATH)
        base_prompt = system_prompt or self._default_system_prompt()
        self._system_prompt = f"{base_prompt}\n{system_prompt_append}" if system_prompt_append else base_prompt
        # Per-backend parser maps the agent's wire output to the common events.
        self._parser = parser
        self._session_id: str | None = None
        self._proc: subprocess.Popen | None = None
        self._reader: threading.Thread | None = None
        # Set by stop() so the reader thread can distinguish a user-requested
        # termination from a real failure and suppress the spurious exit error.
        self._stopped = False
        # Incremented per turn. A reader thread captures its generation at launch
        # and only emits events while it is still current — so a prior reader that
        # outlived its join (e.g. a subprocess that ignored stop()) has its late
        # events, including its exit error, discarded instead of interleaving with
        # the new turn.
        self._generation = 0
        # Guards the shared state above (``_proc``, ``_session_id``, ``_stopped``,
        # ``_generation``) against the reader thread racing the main thread. Only
        # ever held around the trivial reads/writes below — never across a
        # blocking call (join/wait/subprocess read) or an ``on_event`` callback —
        # so it cannot deadlock against the reader it is synchronizing with.
        self._lock = threading.Lock()

    @property
    def session_id(self) -> str | None:
        """Return the captured session id, or ``None`` before the first turn."""
        return self._session_id

    def _default_system_prompt(self) -> str:
        send = os.path.join(self._scripts_dir, "isaacsim_send.py")
        shot = os.path.join(self._scripts_dir, "viewport_screenshot.py")
        return (
            "You are embedded in a running NVIDIA Isaac Sim session and can act on "
            "the live USD stage. The isaacsim.code_editor.python_server socket "
            f"listens on loopback port {self._port}. Execute scene Python by running:\n"
            f"    python3 {send} --port {self._port} '<python source>'\n"
            f"Capture the viewport (only when a visual check is needed) by sending the "
            f"capture script through the same socket client:\n"
            f"    python3 {send} --port {self._port} --file {shot} --arg output_path=/tmp/agent_view.png\n"
            "Prefer cheap stage introspection (does the prim exist? transform? world "
            "bounding box? physics settled?) over screenshots to verify your work. "
            "Use the repository's robotics-sim skills for asset paths and placement."
        )

    @abc.abstractmethod
    def _build_argv(self, text: str) -> list[str]:
        raise NotImplementedError("Subclasses must implement this method")

    def _spawn(self, argv: list[str]) -> subprocess.Popen:
        """Spawn the agent subprocess for one turn.

        A seam so tests can inject a fake process and exercise the reader/parse
        pipeline without launching a real interpreter.

        Args:
            argv: The full launch argv built by :meth:`_build_argv`.

        Returns:
            The spawned process, with line-buffered text stdout/stderr pipes.
        """
        return subprocess.Popen(  # noqa: S603 - argv is built from fixed flags + user text
            argv,
            cwd=self._repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def send(self, text: str, on_event: Callable[[StreamEvent], None]) -> None:
        """Start a turn: spawn the agent and read its output on a daemon thread.

        Args:
            text: The user prompt for this turn.
            on_event: Invoked from the reader thread for each parsed event;
                callers that touch UI must marshal onto the main thread (see
                :class:`~.event_pump.EventPump`).
        """
        with self._lock:
            proc_alive = self._proc is not None and self._proc.poll() is None
        if proc_alive:
            on_event(ErrorEvent(message="A turn is already in progress."))
            return
        # Join a prior turn's reader thread that may still be finishing its finally
        # block (e.g. right after stop()) BEFORE claiming this turn — so it still
        # suppresses its own exit error and its trailing events can't interleave
        # with the new turn. Done WITHOUT the lock, since the reader acquires it.
        reader = self._reader
        if reader is not None and reader.is_alive():
            reader.join(timeout=2.0)
        with self._lock:
            self._stopped = False
            # Claim this turn's generation. If the join above timed out and the old
            # reader is still alive, bumping the generation makes its remaining
            # callbacks no-ops (see _read_loop) so they can't leak into this turn.
            self._generation += 1
            generation = self._generation
        argv = self._build_argv(text)
        try:
            proc = self._spawn(argv)
        except (FileNotFoundError, OSError) as exc:
            on_event(ErrorEvent(message=f"Failed to launch agent ({self._argv0[0]}): {exc}"))
            return
        with self._lock:
            self._proc = proc
        self._reader = threading.Thread(target=self._read_loop, args=(proc, on_event, generation), daemon=True)
        self._reader.start()

    def _read_loop(self, proc: subprocess.Popen, on_event: Callable[[StreamEvent], None], generation: int) -> None:
        # True only while this reader's turn is still the active one; once a newer
        # send() bumps the generation, this reader's events are dropped.
        def is_current() -> bool:
            with self._lock:
                return generation == self._generation

        # Drain stderr concurrently. Reading it only after stdout EOF would
        # deadlock if the child fills the (~64 KB) stderr pipe buffer while we
        # are still blocked reading stdout: the child blocks writing stderr, so
        # it stops producing stdout, so we never reach EOF.
        stderr_chunks: list[str] = []

        def drain_stderr() -> None:
            try:
                for line in proc.stderr:
                    stderr_chunks.append(line)
            except Exception:  # noqa: BLE001 - best-effort capture for the error message
                pass

        stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
        stderr_thread.start()

        try:
            for line in proc.stdout:
                # A parser MUST return [] on bad input rather than raise, but guard
                # anyway: an unexpected exception here would otherwise kill this
                # daemon thread silently, leaving the UI stuck "busy" forever with
                # no error. Surface it, end the turn, and let the finally clean up.
                try:
                    events = self._parser.parse_line(line)
                except Exception as exc:  # noqa: BLE001 - a buggy parser must not wedge the turn
                    if is_current():
                        on_event(ErrorEvent(message=f"Failed to parse agent output: {exc}"))
                    self.stop()  # terminate the child and suppress the follow-on exit error
                    break
                for event in events:
                    if not is_current():
                        continue
                    sid = getattr(event, "session_id", None)
                    if isinstance(event, (InitEvent, ResultEvent)) and sid:
                        with self._lock:
                            self._session_id = sid
                    on_event(event)
        finally:
            try:
                proc.stdout.close()
            except Exception:  # noqa: BLE001
                pass
            returncode = proc.wait()
            stderr_thread.join(timeout=2.0)
            with self._lock:
                current = generation == self._generation
                stopped = self._stopped
            if current and returncode != 0 and not stopped:
                stderr = "".join(stderr_chunks)
                on_event(
                    ErrorEvent(
                        message=f"Agent exited with code {returncode}."
                        + (f"\n{stderr.strip()}" if stderr.strip() else "")
                    )
                )
            try:
                proc.stderr.close()
            except Exception:  # noqa: BLE001
                pass

    def join(self, timeout: float | None = None) -> bool:
        """Wait for the current turn's reader thread to finish.

        Primarily for tests; the UI relies on the ``result`` event instead.

        Args:
            timeout: Maximum seconds to wait, or ``None`` to wait indefinitely.

        Returns:
            ``True`` if the reader finished (or there was none), ``False`` on timeout.
        """
        if self._reader is None:
            return True
        self._reader.join(timeout)
        return not self._reader.is_alive()

    def stop(self) -> None:
        """Terminate the current turn's subprocess, if any."""
        with self._lock:
            self._stopped = True  # tells _read_loop the non-zero exit was user-requested
            # Bump the generation so the reader's in-flight events (anything parsed
            # after this point) become no-ops, not just the exit error — otherwise a
            # late ResultEvent could still drive finalize_turn after the user stopped.
            self._generation += 1
            proc = self._proc
            self._proc = None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:  # noqa: BLE001
                pass
