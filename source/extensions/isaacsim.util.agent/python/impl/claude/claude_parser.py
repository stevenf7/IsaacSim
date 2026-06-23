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

"""Claude Code response parser.

Maps one line of Claude Code's ``--output-format stream-json`` output to the
backend-agnostic events in :mod:`~..stream_events`. This is the Claude-specific
counterpart used by :class:`~.claude_session.ClaudeSession`; other backends
provide their own :class:`~..stream_events.ResponseParser`.

Pure module — no Kit/omni imports — so it is unit-testable in isolation.
"""

from __future__ import annotations

import json

from ..stream_events import (
    AssistantText,
    InitEvent,
    ResponseParser,
    ResultEvent,
    ToolResult,
    ToolUse,
    UnknownEvent,
)


def _content_text(content: object) -> str:
    """Normalize a ``tool_result`` content payload to plain text.

    Claude sends either a bare string or a list of ``{"type": "text", ...}``
    blocks; collapse both to a single string.

    Args:
        content: The raw ``content`` field from a tool_result block.

    Returns:
        The flattened text (empty string when there is nothing to show).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "".join(parts)
    if content is None:
        return ""
    return str(content)


class ClaudeResponseParser(ResponseParser):
    """Parse Claude Code ``stream-json`` lines into typed events."""

    def parse_line(self, line: str) -> list:
        """Parse one stream-json line into zero or more typed events.

        Blank lines and malformed JSON yield ``[]`` (never raises). Recognized
        ``type`` values map to the common event dataclasses; everything else
        becomes a single :class:`~..stream_events.UnknownEvent`.

        Args:
            line: One line of Claude Code ``stream-json`` output.

        Returns:
            The events parsed from the line; ``[]`` for blank or malformed input.
        """
        if not line or not line.strip():
            return []
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            return []
        if not isinstance(obj, dict):
            return []

        etype = obj.get("type")

        if etype == "system":
            if obj.get("subtype") == "init":
                return [InitEvent(session_id=str(obj.get("session_id", "")))]
            return [UnknownEvent(raw=obj)]

        if etype == "assistant":
            events = []
            for block in obj.get("message", {}).get("content", []) or []:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text":
                    events.append(AssistantText(text=str(block.get("text", ""))))
                elif btype == "tool_use":
                    events.append(
                        ToolUse(
                            id=str(block.get("id", "")),
                            name=str(block.get("name", "")),
                            input=block.get("input", {}) or {},
                        )
                    )
            return events

        if etype == "user":
            events = []
            for block in obj.get("message", {}).get("content", []) or []:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                events.append(
                    ToolResult(
                        tool_use_id=str(block.get("tool_use_id", "")),
                        text=_content_text(block.get("content")),
                        is_error=bool(block.get("is_error", False)),
                    )
                )
            return events

        if etype == "result":
            cost = obj.get("total_cost_usd")
            return [
                ResultEvent(
                    text=str(obj.get("result", "")),
                    cost_usd=float(cost) if isinstance(cost, (int, float)) else None,
                    session_id=obj.get("session_id"),
                )
            ]

        return [UnknownEvent(raw=obj)]
