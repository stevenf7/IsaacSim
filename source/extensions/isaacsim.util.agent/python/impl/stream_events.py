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

"""Backend-agnostic typed events + the response-parser interface.

Pure module — no Kit/omni imports — so it is unit-testable in isolation. These
dataclasses are the common event vocabulary every agent backend normalizes to
(consumed by the EventPump and ChatWindow). Each backend supplies a
:class:`ResponseParser` that maps its own wire format to these events; the
Claude Code implementation lives in :mod:`~.claude.claude_parser` (ClaudeResponseParser).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class InitEvent:
    """Emitted once at session start (``system``/``init``)."""

    session_id: str


@dataclass
class AssistantText:
    """A text block from the assistant."""

    text: str


@dataclass
class ToolUse:
    """The assistant invoking a tool (e.g. ``Bash`` running a socket script)."""

    id: str
    name: str
    input: dict


@dataclass
class ToolResult:
    """The result of a tool call, fed back to the assistant."""

    tool_use_id: str
    text: str
    is_error: bool


@dataclass
class ResultEvent:
    """Terminal event for a turn (``result``)."""

    text: str
    cost_usd: float | None
    session_id: str | None


@dataclass
class ErrorEvent:
    """Out-of-band error such as a spawn failure or non-zero exit.

    Not produced by the agent; synthesized by
    :class:`~.agent_session.AgentSession` and rendered like any other event.
    """

    message: str


@dataclass
class UnknownEvent:
    """A line whose ``type`` a parser does not specifically handle.

    Kept (rather than dropped) so the UI can choose to surface it during debugging.
    """

    raw: dict


#: Union of every event a parser may emit and the UI may receive.
StreamEvent = InitEvent | AssistantText | ToolUse | ToolResult | ResultEvent | ErrorEvent | UnknownEvent


class ResponseParser(abc.ABC):
    """Backend parser contract.

    Maps one line of an agent's wire output to a list of the typed events above
    (zero or more — a single line may carry several content blocks). Each
    ``*Session`` backend supplies its own concrete parser; the session's reader
    thread calls :meth:`parse_line` on every stdout line. Implementations MUST
    NOT raise on blank/malformed input — return ``[]`` instead.
    """

    @abc.abstractmethod
    def parse_line(self, line: str) -> list:
        """Map one line of the agent's wire output to zero or more typed events.

        Args:
            line: A single line of the agent's stdout.

        Returns:
            The events parsed from the line; ``[]`` for blank or malformed input.
        """
        raise NotImplementedError("Subclasses must implement parse_line")
