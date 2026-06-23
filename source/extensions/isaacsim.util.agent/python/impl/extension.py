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

"""Extension entry point.

Wires the chat window, agent session, and event pump together and adds a
Window-menu toggle. The panel lives inside Isaac Sim; the agent it spawns drives
*this same* Kit process over the loopback python_server socket, so the user sees
scene changes live in the viewport.
"""

from __future__ import annotations

import os

import carb
import omni.ext
import omni.kit.app
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, refresh_menu_items, remove_menu_items

from .agent_session import AgentSession
from .chat_window import ChatWindow
from .claude.claude_session import ClaudeSession
from .event_pump import EventPump
from .port_discovery import get_python_server_port

_PYTHON_SERVER_EXT = "isaacsim.code_editor.python_server"
_MENU_GROUP = "Window"
_WINDOW_TITLE = "AI Agent Chat"
_SETTINGS_NS = "/exts/isaacsim.util.agent"


def _find_repo_root(start: str) -> str:
    """Walk up from ``start`` to the repo root the agent relies on.

    Prefers the primary marker (the in-repo ``skills/isaac-sim-remote`` the agent
    drives over the socket). If that is never found, falls back to the nearest
    ``.git``/``build.sh`` ancestor, then to ``start`` — and logs a warning, since
    the agent's repo-relative paths (skills, socket scripts) would then be wrong.

    Args:
        start: Directory to begin the upward search from.

    Returns:
        The resolved repo root, or the best-effort fallback described above.
    """
    path = os.path.abspath(start)
    fallback = None
    while True:
        if os.path.isdir(os.path.join(path, "skills", "isaac-sim-remote")):
            return path
        if fallback is None and (
            os.path.isdir(os.path.join(path, ".git")) or os.path.isfile(os.path.join(path, "build.sh"))
        ):
            fallback = path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent

    chosen = fallback or os.path.abspath(start)
    carb.log_warn(
        f"[isaacsim.util.agent] could not find the 'skills/isaac-sim-remote' marker above "
        f"{start!r}; falling back to {chosen!r}. The agent's repo-relative paths may be incorrect."
    )
    return chosen


class AgentChatExtension(omni.ext.IExt):
    """Lifecycle owner for the AI Agent Chat panel."""

    def on_startup(self, ext_id: str) -> None:
        """Build the panel, wire the agent session and pump, and add the menu item.

        Args:
            ext_id: The extension id assigned by the Kit extension manager.
        """
        self._window: ChatWindow | None = None
        self._pump: EventPump | None = None
        self._session: AgentSession | None = None
        self._menu_items = None

        app = omni.kit.app.get_app()
        ext_manager = app.get_extension_manager()

        # The agent acts via the python_server socket, so make sure it is enabled,
        # then read the *actual* port (never assume 8226 — a co-resident instance
        # may have moved it).
        if not ext_manager.is_extension_enabled(_PYTHON_SERVER_EXT):
            try:
                ext_manager.set_extension_enabled_immediate(_PYTHON_SERVER_EXT, True)
            except Exception as exc:  # noqa: BLE001
                carb.log_warn(f"[isaacsim.util.agent] could not enable {_PYTHON_SERVER_EXT}: {exc}")

        settings = carb.settings.get_settings()
        port = get_python_server_port(settings)

        ext_path = ext_manager.get_extension_path(ext_id) or os.getcwd()
        repo_root = _find_repo_root(ext_path)

        # Config-style values come from carb settings (declared in extension.toml)
        # so users can extend the system prompt or adjust tool rules without
        # editing source. Unset list settings read back as None -> backend defaults.
        system_prompt_append = settings.get(f"{_SETTINGS_NS}/system_prompt_append") or ""
        allowed_tools = settings.get(f"{_SETTINGS_NS}/allowed_tools")
        disallowed_tools = settings.get(f"{_SETTINGS_NS}/disallowed_tools")

        # Instantiate the concrete backend. The field is typed against the base
        # AgentSession (above), so future *Session backends (e.g. GeminiSession,
        # CodexSession) drop in by changing only this line / a backend selector.
        # TODO(rhua): add a backend selector.
        self._session = ClaudeSession(
            repo_root=repo_root,
            port=port,
            system_prompt_append=system_prompt_append,
            allowed_tools=list(allowed_tools) if allowed_tools is not None else None,
            disallowed_tools=list(disallowed_tools) if disallowed_tools is not None else None,
        )
        self._window = ChatWindow(
            _WINDOW_TITLE,
            on_send=self._on_send,
            on_stop=self._on_stop,
            on_visibility_changed=self._on_visibility_changed,
        )
        self._pump = EventPump(self._window)
        self._pump.start()
        self._window.set_status(f"Ready. python_server on port {port}; repo: {repo_root}")

        self._menu_items = [
            MenuItemDescription(
                name=_WINDOW_TITLE,
                ticked=True,
                ticked_fn=self._is_window_visible,
                onclick_fn=self._toggle_window,
            )
        ]
        add_menu_items(self._menu_items, _MENU_GROUP)

    def on_shutdown(self) -> None:
        """Tear down the menu item, agent session, pump, and window."""
        if self._menu_items:
            remove_menu_items(self._menu_items, _MENU_GROUP)
            self._menu_items = None
        if self._session:
            self._session.stop()
            self._session = None
        if self._pump:
            self._pump.stop()
            self._pump = None
        if self._window:
            self._window.destroy()
            self._window = None

    # ----- callbacks -------------------------------------------------------

    def _on_send(self, text: str) -> None:
        if self._session and self._pump:
            self._session.send(text, self._pump.on_event)

    def _on_stop(self) -> None:
        if self._session:
            self._session.stop()
        # stop() halts further reader emissions; also drop anything already queued
        # for the stopped turn so a late event can't render after "Stopped.".
        if self._pump:
            self._pump.discard_pending()

    def _is_window_visible(self) -> bool:
        return bool(self._window) and self._window.visible

    def _toggle_window(self, *_args: object) -> None:
        if self._window:
            self._window.set_visible(not self._window.visible)

    def _on_visibility_changed(self, _visible: bool) -> None:
        # Keep the Window-menu checkmark in sync when the panel is closed via its
        # title-bar X (not just via the menu toggle).
        refresh_menu_items(_MENU_GROUP)
