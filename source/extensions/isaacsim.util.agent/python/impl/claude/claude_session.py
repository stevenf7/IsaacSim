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

"""Claude Code session — the concrete AgentSession backend for ``claude -p``."""

from __future__ import annotations

import os

from ..agent_session import AgentSession
from .claude_parser import ClaudeResponseParser

#: Default allow rules for the agent's tools, beyond the mandatory in-repo
#: socket-driver Bash rule that :meth:`ClaudeSession._allowed_tools` always adds.
#: Mirrors the ``allowed_tools`` default declared in ``config/extension.toml``.
DEFAULT_ALLOWED_TOOLS = ["Read(**)", "Glob(**)", "Grep(**)", "Skill"]

#: Default deny rules (block the agent's own file tools from absolute paths).
#: Cosmetic — see the class warning. Mirrors ``disallowed_tools`` in extension.toml.
DEFAULT_DISALLOWED_TOOLS = ["Read(//**)", "Glob(//**)", "Grep(//**)"]


class ClaudeSession(AgentSession):
    """Claude Code backend: build the ``claude -p`` argv and parse its stream-json.

    .. warning::
        The tool allow/deny rules below are **not** a security boundary. The
        agent's whole purpose is to send arbitrary Python through
        ``isaacsim_send.py`` into this Kit process, which has full filesystem
        and network access — so it can read ``~/.ssh``, reach the network, or
        touch anything this process can, regardless of these rules. The real
        boundary for a productized panel is the **OS sandbox** (restricted
        filesystem + network egress); only run the panel in an environment you
        would trust the agent to act in.

    Args:
        repo_root: Working directory for the agent subprocess.
        port: The python_server loopback port handed to the agent.
        agent_path: Path to (or name of) the ``claude`` executable.
        system_prompt: Full system-prompt override; falls back to the built-in
            default when ``None``.
        system_prompt_append: Extra text appended to the system prompt.
        allowed_tools: Tool allow rules beyond the mandatory socket-driver Bash
            rule; ``None`` uses :data:`DEFAULT_ALLOWED_TOOLS`.
        disallowed_tools: Tool deny rules; ``None`` uses :data:`DEFAULT_DISALLOWED_TOOLS`.
    """

    def __init__(
        self,
        repo_root: str,
        port: int,
        agent_path: str = "claude",
        system_prompt: str | None = None,
        system_prompt_append: str = "",
        allowed_tools: list[str] | None = None,
        disallowed_tools: list[str] | None = None,
    ) -> None:
        super().__init__(
            repo_root,
            port,
            agent_path=agent_path,
            system_prompt=system_prompt,
            system_prompt_append=system_prompt_append,
            parser=ClaudeResponseParser(),
        )
        # Copy so a passed-in list can't mutate under us; fall back to the defaults.
        self._extra_allowed_tools = list(allowed_tools) if allowed_tools is not None else list(DEFAULT_ALLOWED_TOOLS)
        self._disallowed_tools = (
            list(disallowed_tools) if disallowed_tools is not None else list(DEFAULT_DISALLOWED_TOOLS)
        )

    def _allowed_tools(self) -> list[str]:
        """Build the ``--allowedTools`` rules, pinned to the in-repo socket driver.

        Returns:
            The allow rules; the resolved ``isaacsim_send.py`` Bash rule is always
            first (the panel needs it), followed by the configured allow rules.
        """
        send_script = os.path.join(self._scripts_dir, "isaacsim_send.py")
        # Pin Bash to the resolved driver path instead of ``*isaacsim_send*`` (which
        # would match e.g. ``python3 -c '...'  # isaacsim_send``). Residual gap:
        # Claude's Bash matcher is prefix-based, so shell metacharacters after the
        # path (``;``, ``&&``, pipes) can still chain other commands — this narrows,
        # but does not seal, the surface. Real containment is the OS sandbox.
        return [f"Bash(python3 {send_script}*)", *self._extra_allowed_tools]

    def _build_argv(self, text: str) -> list[str]:
        argv = [
            *self._argv0,
            "-p",
            text,
            "--output-format",
            "stream-json",
            "--verbose",
            "--add-dir",
            self._repo_root,
            "--allowedTools",
            *self._allowed_tools(),
            "--disallowedTools",
            *self._disallowed_tools,
            "--append-system-prompt",
            self._system_prompt,
        ]
        if self._session_id:
            argv += ["--resume", self._session_id]
        return argv
