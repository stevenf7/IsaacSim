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

"""Unit tests for the Claude Code stream-json response parser."""

import json

import omni.kit.test
from isaacsim.util.agent.impl.claude.claude_parser import ClaudeResponseParser
from isaacsim.util.agent.impl.stream_events import (
    AssistantText,
    InitEvent,
    ResultEvent,
    ToolResult,
    ToolUse,
    UnknownEvent,
)


class TestClaudeResponseParser(omni.kit.test.AsyncTestCase):
    """Mapping of stream-json lines to the backend-agnostic event types."""

    def setUp(self) -> None:
        """Create a fresh parser for each test."""
        self.parser = ClaudeResponseParser()

    async def test_init_event(self) -> None:
        """A ``system``/``init`` line yields an InitEvent with the session id."""
        events = self.parser.parse_line(json.dumps({"type": "system", "subtype": "init", "session_id": "abc"}))
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], InitEvent)
        self.assertEqual(events[0].session_id, "abc")

    async def test_assistant_text(self) -> None:
        """An assistant text block yields a single AssistantText."""
        line = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}})
        events = self.parser.parse_line(line)
        self.assertEqual([type(e) for e in events], [AssistantText])
        self.assertEqual(events[0].text, "hi")

    async def test_assistant_text_and_tool_use_in_one_line(self) -> None:
        """One assistant line with text + tool_use blocks yields both events in order."""
        line = json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "running"},
                        {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}},
                    ]
                },
            }
        )
        events = self.parser.parse_line(line)
        self.assertEqual([type(e) for e in events], [AssistantText, ToolUse])
        self.assertEqual(events[1].id, "t1")
        self.assertEqual(events[1].name, "Bash")
        self.assertEqual(events[1].input, {"command": "ls"})

    async def test_tool_result_string_content(self) -> None:
        """A tool_result with bare-string content yields a ToolResult."""
        line = json.dumps(
            {
                "type": "user",
                "message": {
                    "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok", "is_error": False}]
                },
            }
        )
        events = self.parser.parse_line(line)
        self.assertEqual([type(e) for e in events], [ToolResult])
        self.assertEqual(events[0].tool_use_id, "t1")
        self.assertEqual(events[0].text, "ok")
        self.assertFalse(events[0].is_error)

    async def test_tool_result_list_content_and_error(self) -> None:
        """A tool_result with list content is flattened and ``is_error`` preserved."""
        line = json.dumps(
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "t2",
                            "content": [{"type": "text", "text": "boom"}],
                            "is_error": True,
                        }
                    ]
                },
            }
        )
        events = self.parser.parse_line(line)
        self.assertEqual(events[0].text, "boom")
        self.assertTrue(events[0].is_error)

    async def test_result_event(self) -> None:
        """A ``result`` line yields a ResultEvent with text, cost, and session id."""
        line = json.dumps(
            {"type": "result", "subtype": "success", "result": "done", "total_cost_usd": 0.5, "session_id": "s9"}
        )
        events = self.parser.parse_line(line)
        self.assertEqual([type(e) for e in events], [ResultEvent])
        self.assertEqual(events[0].text, "done")
        self.assertEqual(events[0].cost_usd, 0.5)
        self.assertEqual(events[0].session_id, "s9")

    async def test_unknown_type(self) -> None:
        """An unrecognized ``type`` becomes a single UnknownEvent."""
        events = self.parser.parse_line(json.dumps({"type": "something_new", "foo": 1}))
        self.assertEqual([type(e) for e in events], [UnknownEvent])

    async def test_blank_and_malformed_return_empty(self) -> None:
        """Blank lines and malformed/non-object JSON yield an empty list."""
        self.assertEqual(self.parser.parse_line(""), [])
        self.assertEqual(self.parser.parse_line("   \n"), [])
        self.assertEqual(self.parser.parse_line("{not json"), [])
        self.assertEqual(self.parser.parse_line("42"), [])  # valid JSON, not an object
