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

"""Unit tests for the EventPump queue/drain/dispatch logic."""

import omni.kit.test
from isaacsim.util.agent.impl.event_pump import EventPump
from isaacsim.util.agent.impl.stream_events import (
    AssistantText,
    ErrorEvent,
    InitEvent,
    ResultEvent,
    ToolResult,
    ToolUse,
    UnknownEvent,
)


class _FakeWindow:
    """Records the dispatch calls EventPump makes, in order."""

    def __init__(self) -> None:
        self.calls: list = []

    def append_assistant_text(self, text: str) -> None:
        self.calls.append(("text", text))

    def add_tool_row(self, tool_id: str, name: str, tool_input: dict) -> None:
        self.calls.append(("tool", tool_id, name, tool_input))

    def attach_tool_result(self, tool_use_id: str, text: str, is_error: bool) -> None:
        self.calls.append(("tool_result", tool_use_id, text, is_error))

    def finalize_turn(self, event: object) -> None:
        self.calls.append(("finalize", event))

    def show_error(self, message: str) -> None:
        self.calls.append(("error", message))

    def scroll_to_bottom(self) -> None:
        self.calls.append(("scroll",))


class TestEventPump(omni.kit.test.AsyncTestCase):
    """Queueing and main-thread dispatch behavior."""

    async def test_on_event_is_deferred_until_drain(self) -> None:
        """on_event only enqueues; nothing reaches the window until a drain runs."""
        window = _FakeWindow()
        pump = EventPump(window)
        pump.on_event(AssistantText(text="hi"))
        self.assertEqual(window.calls, [])
        pump._drain(None)  # noqa: SLF001 - drive the per-frame drain directly
        self.assertEqual(window.calls, [("text", "hi")])

    async def test_dispatch_routes_each_event_type(self) -> None:
        """Each event type is routed to its matching window method, in order."""
        window = _FakeWindow()
        pump = EventPump(window)
        result = ResultEvent(text="done", cost_usd=0.1, session_id="s")
        # InitEvent and UnknownEvent render nothing, so they must not appear below.
        for event in [
            InitEvent(session_id="s"),
            AssistantText(text="a"),
            ToolUse(id="t1", name="Bash", input={"command": "ls"}),
            ToolResult(tool_use_id="t1", text="ok", is_error=False),
            UnknownEvent(raw={}),
            result,
            ErrorEvent(message="boom"),
        ]:
            pump.on_event(event)
        pump._drain(None)  # noqa: SLF001
        self.assertEqual(
            window.calls,
            [
                ("text", "a"),
                ("tool", "t1", "Bash", {"command": "ls"}),
                ("tool_result", "t1", "ok", False),
                ("finalize", result),
                ("error", "boom"),
            ],
        )

    async def test_scroll_requested_on_following_drain(self) -> None:
        """A drain that dispatched content scrolls to the bottom on the next drain."""
        window = _FakeWindow()
        pump = EventPump(window)
        pump.on_event(AssistantText(text="x"))
        pump._drain(None)  # noqa: SLF001 - dispatches content, marks a pending scroll
        self.assertNotIn(("scroll",), window.calls)
        pump._drain(None)  # noqa: SLF001 - next frame performs the pending scroll
        self.assertIn(("scroll",), window.calls)

    async def test_discard_pending_drops_queued_events(self) -> None:
        """discard_pending() drops queued events so a stopped turn can't still render."""
        window = _FakeWindow()
        pump = EventPump(window)
        pump.on_event(AssistantText(text="late"))
        pump.on_event(ResultEvent(text="done", cost_usd=0.1, session_id="s"))
        pump.discard_pending()
        pump._drain(None)  # noqa: SLF001
        self.assertEqual(window.calls, [])
