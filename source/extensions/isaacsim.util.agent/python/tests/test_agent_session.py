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

"""Tests for the base AgentSession machinery and Claude argv construction."""

import json
import os
import threading
from collections.abc import Callable, Iterator

import omni.kit.test
from isaacsim.util.agent.impl.agent_session import AgentSession
from isaacsim.util.agent.impl.claude.claude_parser import ClaudeResponseParser
from isaacsim.util.agent.impl.claude.claude_session import ClaudeSession
from isaacsim.util.agent.impl.stream_events import (
    AssistantText,
    ErrorEvent,
    InitEvent,
    ResultEvent,
    ToolResult,
    ToolUse,
)


class _FakeStream:
    """A minimal stand-in for ``proc.stdout``/``proc.stderr``: iterable + closable.

    Args:
        lines: The lines yielded when iterated.
    """

    def __init__(self, lines: list) -> None:
        self._lines = list(lines)

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)

    def close(self) -> None:
        pass


class _CannedProc:
    """A fake process that emits canned stdout lines, then exits with ``returncode``.

    Args:
        stdout_lines: The stdout lines the reader will consume.
        returncode: The exit code reported by :meth:`wait`/:meth:`poll`.
    """

    def __init__(self, stdout_lines: list, returncode: int = 0) -> None:
        self.stdout = _FakeStream(stdout_lines)
        self.stderr = _FakeStream([])
        self._returncode = returncode
        self._done = False

    def poll(self) -> int | None:
        return self._returncode if self._done else None

    def wait(self) -> int:
        self._done = True
        return self._returncode

    def terminate(self) -> None:
        self._done = True


class _BlockingProc:
    """A fake process whose stdout blocks until :meth:`terminate` is called."""

    def __init__(self) -> None:
        self._event = threading.Event()
        self._done = False
        self.stderr = _FakeStream([])
        self.stdout = self  # iterating stdout blocks until terminate()

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        self._event.wait()
        raise StopIteration

    def close(self) -> None:
        pass

    def poll(self) -> int | None:
        return -15 if self._done else None

    def wait(self) -> int:
        self._event.wait()
        self._done = True
        return -15

    def terminate(self) -> None:
        self._done = True
        self._event.set()


def _canned_lines(argv: list) -> list:
    """Build a canned Claude stream-json turn from the launch argv.

    Args:
        argv: The launch argv; its ``-p`` prompt and ``--resume`` presence are
            reflected in the emitted assistant text.

    Returns:
        The stream-json lines (newline-terminated) for one full turn.
    """
    resumed = "--resume" in argv
    prompt = argv[argv.index("-p") + 1] if "-p" in argv else ""
    text = "resumed" if resumed else "fresh"
    objs = [
        {"type": "system", "subtype": "init", "session_id": "fake-session-123"},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": f"{text}: {prompt}"}]}},
        {
            "type": "assistant",
            "message": {"content": [{"type": "tool_use", "id": "tool-1", "name": "Bash", "input": {"command": "x"}}]},
        },
        {
            "type": "user",
            "message": {
                "content": [{"type": "tool_result", "tool_use_id": "tool-1", "content": "ok", "is_error": False}]
            },
        },
        {
            "type": "result",
            "subtype": "success",
            "result": "Done.",
            "total_cost_usd": 0.0123,
            "session_id": "fake-session-123",
        },
    ]
    return [json.dumps(o) + "\n" for o in objs]


class _FakeSpawnSession(AgentSession):
    """Concrete session whose subprocess is an in-process fake (no real interpreter).

    The reader thread, parser, lock, and session-id capture are exercised for real;
    only the spawned process object is faked, so the tests are deterministic and
    portable (a real ``sys.executable`` is not a usable Python under Kit on Windows).

    Args:
        make_proc: Callable mapping the built argv to a fake process to "spawn".
    """

    def __init__(self, make_proc: Callable[[list[str]], object]) -> None:
        super().__init__("/repo", 8231, agent_path="fake-agent", parser=ClaudeResponseParser())
        self._make_proc = make_proc

    def _build_argv(self, text: str) -> list[str]:
        argv = ["fake-agent", "-p", text]
        if self._session_id:
            argv += ["--resume", self._session_id]
        return argv

    def _spawn(self, argv: list[str]) -> object:
        return self._make_proc(argv)


class _RealSpawnSession(AgentSession):
    """Concrete session that does a real spawn — for the launch-failure path only.

    Args:
        command: The launch argv; point it at a nonexistent path to force failure.
    """

    def __init__(self, command: list) -> None:
        super().__init__("/repo", 8231, agent_path=command[0], parser=ClaudeResponseParser())
        self._command = command

    def _build_argv(self, text: str) -> list[str]:
        return [*self._command, "-p", text]


class _RaisingParser(ClaudeResponseParser):
    """A parser that violates the contract by raising, to test the reader guard."""

    def parse_line(self, line: str) -> list:
        raise RuntimeError("boom")


class TestAgentSession(omni.kit.test.AsyncTestCase):
    """Base-class machinery, driven by in-process fake processes."""

    async def test_single_turn_event_sequence(self) -> None:
        """A full turn emits init -> text -> tool_use -> tool_result -> result."""
        session = _FakeSpawnSession(lambda argv: _CannedProc(_canned_lines(argv)))
        events = []
        session.send("place a forklift at x=3", events.append)
        self.assertTrue(session.join(timeout=15.0), "reader thread did not finish")

        types = [type(e) for e in events]
        self.assertEqual(types, [InitEvent, AssistantText, ToolUse, ToolResult, ResultEvent])
        self.assertEqual(session.session_id, "fake-session-123")

        assistant = next(e for e in events if isinstance(e, AssistantText))
        self.assertIn("fresh", assistant.text)
        tool = next(e for e in events if isinstance(e, ToolUse))
        self.assertEqual(tool.name, "Bash")
        result = next(e for e in events if isinstance(e, ResultEvent))
        self.assertEqual(result.cost_usd, 0.0123)

    async def test_second_turn_resumes(self) -> None:
        """The captured session id flows into the next turn's ``--resume`` argv."""
        session = _FakeSpawnSession(lambda argv: _CannedProc(_canned_lines(argv)))
        first = []
        session.send("turn one", first.append)
        self.assertTrue(session.join(timeout=15.0))
        # The base captures session_id from the init/result events of turn one.
        self.assertEqual(session.session_id, "fake-session-123")

        # The captured id flows into the next turn's argv, and the fake reports "resumed".
        second = []
        session.send("turn two", second.append)
        self.assertTrue(session.join(timeout=15.0))
        assistant = next(e for e in second if isinstance(e, AssistantText))
        self.assertIn("resumed", assistant.text)

    async def test_missing_binary_emits_error_not_raise(self) -> None:
        """A missing agent binary surfaces an ErrorEvent instead of raising."""
        session = _RealSpawnSession(command=["/nonexistent/definitely-not-an-agent"])
        events = []
        session.send("hello", events.append)
        session.join(timeout=15.0)
        self.assertTrue(any(isinstance(e, ErrorEvent) for e in events))

    async def test_stop_suppresses_spurious_exit_error(self) -> None:
        """A user-requested stop() does not surface the resulting non-zero-exit error."""
        # The fake's stdout blocks until terminate(); stop() ends it -> non-zero exit,
        # but the reader must NOT emit an ErrorEvent since the stop was user-requested.
        proc = _BlockingProc()
        session = _FakeSpawnSession(lambda argv: proc)
        events = []
        session.send("hello", events.append)
        session.stop()
        self.assertTrue(session.join(timeout=15.0))
        self.assertFalse(
            any(isinstance(e, ErrorEvent) for e in events),
            "stop() should suppress the spurious non-zero-exit error",
        )

    async def test_parser_exception_emits_error_and_ends_turn(self) -> None:
        """A parser that raises surfaces an ErrorEvent and the reader finishes (no hang)."""
        session = _FakeSpawnSession(lambda argv: _CannedProc(_canned_lines(argv)))
        session._parser = _RaisingParser()  # noqa: SLF001 - inject a contract-violating parser
        events = []
        session.send("hello", events.append)
        self.assertTrue(session.join(timeout=15.0), "reader thread did not finish after parser error")
        errors = [e for e in events if isinstance(e, ErrorEvent)]
        self.assertEqual(len(errors), 1, "expected exactly one parse-failure error")
        self.assertIn("parse agent output", errors[0].message)

    async def test_stop_invalidates_current_generation(self) -> None:
        """stop() bumps the generation so the stopped turn's late events become no-ops."""
        proc = _BlockingProc()
        session = _FakeSpawnSession(lambda argv: proc)
        session.send("hello", lambda _e: None)
        gen_before = session._generation  # noqa: SLF001
        session.stop()
        self.assertGreater(session._generation, gen_before)  # noqa: SLF001
        session.join(timeout=15.0)


class TestClaudeSession(omni.kit.test.AsyncTestCase):
    """Claude-specific argv construction (pure unit — no subprocess)."""

    async def test_build_argv_has_claude_flags_and_allowlist(self) -> None:
        """The Claude argv carries the expected flags and the socket-script allowlist."""
        session = ClaudeSession(repo_root="/repo", port=8231, agent_path="claude")
        argv = session._build_argv("hello")  # noqa: SLF001 - white-box check of the flag wiring
        for flag in ("-p", "--output-format", "stream-json", "--verbose", "--add-dir", "--append-system-prompt"):
            self.assertIn(flag, argv)
        # Bash is pinned to the resolved in-repo driver path, not a bare substring.
        expected_send = os.path.join("/repo", "skills", "isaac-sim-remote", "scripts", "isaacsim_send.py")
        self.assertIn(f"Bash(python3 {expected_send}*)", argv)
        self.assertNotIn("Bash(python3 *isaacsim_send*)", argv)
        self.assertNotIn("--resume", argv)  # no session yet

    async def test_build_argv_adds_resume_after_session_id(self) -> None:
        """A captured session id adds ``--resume <id>`` to the argv."""
        session = ClaudeSession(repo_root="/repo", port=8231, agent_path="claude")
        session._session_id = "sess-42"  # noqa: SLF001 - simulate a captured session id
        argv = session._build_argv("again")  # noqa: SLF001
        self.assertIn("--resume", argv)
        self.assertEqual(argv[argv.index("--resume") + 1], "sess-42")

    async def test_system_prompt_append_extends_default(self) -> None:
        """system_prompt_append is appended after the built-in default prompt."""
        session = ClaudeSession(repo_root="/repo", port=8231, system_prompt_append="EXTRA PROJECT RULES")
        prompt = session._system_prompt  # noqa: SLF001
        self.assertIn("isaacsim.code_editor.python_server", prompt)  # built-in retained
        self.assertTrue(prompt.endswith("EXTRA PROJECT RULES"))

    async def test_full_override_then_append(self) -> None:
        """A full system_prompt override is used as the base, then appended to."""
        session = ClaudeSession(repo_root="/repo", port=8231, system_prompt="BASE PROMPT", system_prompt_append="MORE")
        self.assertEqual(session._system_prompt, "BASE PROMPT\nMORE")  # noqa: SLF001

    async def test_tool_defaults_when_unset(self) -> None:
        """With no tool settings, the built-in allow/deny defaults are used."""
        argv = ClaudeSession(repo_root="/repo", port=8231)._build_argv("hi")  # noqa: SLF001
        for tool in ("Read(**)", "Glob(**)", "Grep(**)", "Skill"):
            self.assertIn(tool, argv)
        for tool in ("Read(//**)", "Glob(//**)", "Grep(//**)"):
            self.assertIn(tool, argv)

    async def test_configurable_allowed_tools_keep_mandatory_bash_pin(self) -> None:
        """Custom allowed_tools replace the defaults but the socket-driver Bash rule stays."""
        session = ClaudeSession(repo_root="/repo", port=8231, allowed_tools=["Read(**)", "WebFetch"])
        argv = session._build_argv("hi")  # noqa: SLF001
        expected_send = os.path.join("/repo", "skills", "isaac-sim-remote", "scripts", "isaacsim_send.py")
        self.assertIn(f"Bash(python3 {expected_send}*)", argv)  # always injected
        self.assertIn("WebFetch", argv)
        self.assertNotIn("Skill", argv)  # default list was replaced

    async def test_configurable_disallowed_tools(self) -> None:
        """Custom disallowed_tools replace the deny defaults."""
        argv = ClaudeSession(  # noqa: SLF001
            repo_root="/repo", port=8231, disallowed_tools=["Write(//**)"]
        )._build_argv("hi")
        self.assertIn("Write(//**)", argv)
        self.assertNotIn("Read(//**)", argv)

    async def test_empty_allowed_tools_setting_is_respected(self) -> None:
        """An explicit empty allow list still keeps only the mandatory Bash pin."""
        session = ClaudeSession(repo_root="/repo", port=8231, allowed_tools=[])
        argv = session._build_argv("hi")  # noqa: SLF001
        flag = argv.index("--allowedTools")
        # Exactly one allow rule (the Bash pin) sits between the flag and the next flag.
        self.assertEqual(argv[flag + 1 : flag + 3][1], "--disallowedTools")
