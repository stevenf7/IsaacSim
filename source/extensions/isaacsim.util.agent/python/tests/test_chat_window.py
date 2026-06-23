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

"""Unit tests for chat-window helpers."""

import omni.kit.test
from isaacsim.util.agent.impl.chat_window import _done_status, _result_snippet, _tool_label


class TestToolLabel(omni.kit.test.AsyncTestCase):
    """Tool-row label construction (regression coverage for the rstrip bug)."""

    async def test_label_with_command_detail(self) -> None:
        """The command is shown after the tool name."""
        self.assertEqual(_tool_label("Bash", {"command": "ls"}), "[tool] Bash: ls")

    async def test_label_prefers_command_then_file_path(self) -> None:
        """file_path is used as the detail when there is no command."""
        self.assertEqual(_tool_label("Read", {"file_path": "/a/b.py"}), "[tool] Read: /a/b.py")

    async def test_label_without_detail_has_no_trailing_separator(self) -> None:
        """An empty detail yields just the tool name with no dangling ``: ``."""
        self.assertEqual(_tool_label("Skill", {}), "[tool] Skill")
        self.assertEqual(_tool_label("Skill", {"command": ""}), "[tool] Skill")
        self.assertEqual(_tool_label("Skill", "not-a-dict"), "[tool] Skill")

    async def test_detail_ending_in_colon_or_space_is_preserved(self) -> None:
        """A detail ending in ':' or a space is not truncated (the rstrip bug)."""
        self.assertEqual(_tool_label("Bash", {"command": "echo hi "}), "[tool] Bash: echo hi ")
        self.assertEqual(_tool_label("Bash", {"command": "ls:"}), "[tool] Bash: ls:")


class TestResultSnippet(omni.kit.test.AsyncTestCase):
    """First-line extraction and length capping for tool results."""

    async def test_first_line_only(self) -> None:
        """Only the first non-empty line is shown."""
        self.assertEqual(_result_snippet("line1\nline2\nline3"), "line1")

    async def test_empty_text_yields_empty(self) -> None:
        """Whitespace-only output collapses to an empty snippet."""
        self.assertEqual(_result_snippet("   \n  "), "")

    async def test_truncates_beyond_limit(self) -> None:
        """A line longer than the limit is truncated with an ellipsis."""
        self.assertEqual(_result_snippet("x" * 250), "x" * 200 + "...")
        self.assertEqual(_result_snippet("abcdef", limit=3), "abc...")


class TestDoneStatus(omni.kit.test.AsyncTestCase):
    """End-of-turn status string, with and without a reported cost."""

    async def test_with_float_cost(self) -> None:
        """A float cost is formatted to four decimal places."""
        self.assertEqual(_done_status(0.0123), "Done. ($0.0123)")

    async def test_with_int_cost(self) -> None:
        """An int cost is accepted (matches the parser's numeric guard)."""
        self.assertEqual(_done_status(0), "Done. ($0.0000)")

    async def test_without_cost(self) -> None:
        """A missing/None cost yields a bare Done."""
        self.assertEqual(_done_status(None), "Done.")
