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

"""The chat panel UI: a scrolling transcript plus a prompt box and Send/Stop.

All methods here run on the main thread (invoked by :class:`~.event_pump.EventPump`
or directly from button callbacks). The window holds no agent logic — it calls
the ``on_send`` / ``on_stop`` callbacks supplied by the extension.
"""

from __future__ import annotations

from collections.abc import Callable

import omni.ui as ui

from .stream_events import ResultEvent

# Shared dark background so the transcript matches the input field's block.
_PANEL_BG = 0xFF23211F  # warm dark gray

_USER_STYLE = {"color": 0xFFCCE8CC, "margin": 4}  # pale mint green
_ASSISTANT_STYLE = {"color": 0xFFEEEEEE, "margin": 4}  # light gray
_TOOL_STYLE = {"color": 0xFF9FD0FF, "margin_height": 2, "margin_width": 12}  # sky blue
_TOOL_RESULT_STYLE = {"color": 0xFFA0A0A0, "margin_height": 2, "margin_width": 24}  # medium gray
_ERROR_STYLE = {"color": 0xFF5050FF, "margin": 4}  # light red
_STATUS_STYLE = {"color": 0xFF808080, "margin": 4}  # mid gray


def _tool_label(name: str, tool_input: dict) -> str:
    """Build the compact transcript label for a tool call.

    Args:
        name: The tool name (e.g. ``Bash``).
        tool_input: The tool's input payload; its ``command``/``file_path`` is
            shown as a short detail when present.

    Returns:
        ``[tool] <name>: <detail>`` when there is a detail, else ``[tool] <name>``.
    """
    detail = ""
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command") or tool_input.get("file_path") or ""
        detail = str(cmd)
    # Build conditionally rather than stripping a trailing ": ": rstrip(": ")
    # strips a *character set*, so a detail ending in ':' or a space would be
    # silently truncated.
    return f"[tool] {name}: {detail}" if detail else f"[tool] {name}"


def _result_snippet(text: str, limit: int = 200) -> str:
    """Reduce a tool result to a single, length-capped transcript line.

    Args:
        text: The full tool output.
        limit: Maximum characters to show before an ellipsis is appended.

    Returns:
        The first non-empty line, truncated to ``limit`` characters with a
        trailing ``...`` when longer; an empty string when there is no content.
    """
    stripped = text.strip()
    snippet = stripped.splitlines()[0] if stripped else ""
    if len(snippet) > limit:
        snippet = snippet[:limit] + "..."
    return snippet


def _done_status(cost: object) -> str:
    """Build the end-of-turn status line, including cost when available.

    Args:
        cost: The turn's cost in USD, or ``None`` when the backend did not report one.

    Returns:
        ``Done. ($<cost>)`` when ``cost`` is numeric, else ``Done.``.
    """
    # Match the parser's own numeric guard (claude_parser accepts int or float).
    return f"Done. (${cost:.4f})" if isinstance(cost, (int, float)) else "Done."


class ChatWindow:
    """omni.ui chat panel. Pure view — agent wiring lives in the extension.

    Args:
        title: The window title.
        on_send: Called with the prompt text when the user sends a message.
        on_stop: Called when the user clicks Stop.
        on_visibility_changed: Called with the new visibility when the panel is
            shown or hidden; pass ``None`` to skip the subscription.
    """

    def __init__(
        self,
        title: str,
        on_send: Callable[[str], None],
        on_stop: Callable[[], None],
        on_visibility_changed: Callable[[bool], None] | None = None,
    ) -> None:
        self._on_send = on_send
        self._on_stop = on_stop
        self._transcript: ui.VStack | None = None
        self._input: ui.StringField | None = None
        self._send_btn: ui.Button | None = None
        self._stop_btn: ui.Button | None = None
        self._status: ui.Label | None = None
        self._current_assistant: ui.Label | None = None
        self._assistant_chunks: list[str] = []
        self._scroll: ui.ScrollingFrame | None = None
        self._pending_status = ""

        # Start hidden — the panel is opened on demand from the Window menu, not
        # at startup. The frame builds lazily on first show (set_build_fn).
        self._window = ui.Window(title, width=520, height=760, visible=False)
        self._window.frame.set_build_fn(self._build)
        if on_visibility_changed is not None:
            self._window.set_visibility_changed_fn(on_visibility_changed)

    # ----- lifecycle -------------------------------------------------------

    @property
    def window(self) -> ui.Window:
        """Return the underlying :class:`omni.ui.Window`."""
        return self._window

    @property
    def visible(self) -> bool:
        """Return whether the panel is currently visible."""
        return bool(self._window) and self._window.visible

    def set_visible(self, value: bool) -> None:
        """Show or hide the panel.

        Args:
            value: ``True`` to show the panel, ``False`` to hide it.
        """
        if self._window:
            self._window.visible = value

    def destroy(self) -> None:
        """Destroy the underlying window and release its references."""
        if self._window:
            self._window.destroy()
        self._window = None
        self._transcript = None

    # ----- build -----------------------------------------------------------

    def _build(self) -> None:
        with ui.VStack(spacing=4):
            # The transcript MUST be the flexible child (height=Fraction(1)) so it
            # absorbs all spare vertical space; otherwise it sizes to its content and
            # pushes the fixed input row below the window bottom (the row then only
            # appears after the user enlarges the window). Fraction(1) pins the input
            # row to the bottom at any window size.
            self._scroll = ui.ScrollingFrame(
                height=ui.Fraction(1),
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                style={"background_color": _PANEL_BG},
            )
            with self._scroll:
                self._transcript = ui.VStack(spacing=2, height=0)
            self._status = ui.Label(self._pending_status, style=_STATUS_STYLE, height=0)
            # Fixed-height input area pinned at the bottom: the multiline field on
            # top, the Send/Stop row *beneath* it (below — not beside — the field) so
            # the buttons are always visible regardless of window width. (Placing the
            # buttons beside a width=Fraction(1) field let the field overflow and push
            # the button column off the right edge.) The field fills the remaining
            # height of this fixed area. omni.ui's editable multiline field does not
            # word-wrap on kit-kernel 110.1.1; long unbroken lines scroll and Enter
            # inserts newlines.
            with ui.VStack(height=ui.Pixel(118), spacing=4):
                self._input = ui.StringField(
                    multiline=True,
                    height=ui.Fraction(1),
                    style={"background_color": _PANEL_BG},
                )
                with ui.HStack(height=ui.Pixel(30), spacing=6):
                    self._send_btn = ui.Button("Send", clicked_fn=self._handle_send)
                    self._stop_btn = ui.Button("Stop", enabled=False, clicked_fn=self._handle_stop)

    # ----- input handling --------------------------------------------------

    def _handle_send(self) -> None:
        if self._input is None:
            return
        text = self._input.model.get_value_as_string().strip()
        if not text:
            return
        self._input.model.set_value("")
        self.add_user_bubble(text)
        self._current_assistant = None
        self.set_busy(True)
        self._on_send(text)

    def _handle_stop(self) -> None:
        self._on_stop()
        self.set_status("Stopped.")
        self.set_busy(False)

    def set_busy(self, busy: bool) -> None:
        """Enable or disable the input controls for an in-flight turn.

        Args:
            busy: ``True`` while the agent is working (disables Send/input,
                enables Stop), ``False`` when idle.
        """
        if self._send_btn:
            self._send_btn.enabled = not busy
        if self._stop_btn:
            self._stop_btn.enabled = busy
        if self._input:
            self._input.enabled = not busy
        if busy:
            self.set_status("Agent working...")

    def set_status(self, text: str) -> None:
        """Set the status-line text.

        Args:
            text: The status text; preserved and applied later if the panel has
                not been built yet.
        """
        self._pending_status = text  # preserved if the panel hasn't been built/shown yet
        if self._status:
            self._status.text = text

    # ----- transcript mutations (main thread) ------------------------------

    def add_user_bubble(self, text: str) -> None:
        """Append a user message bubble to the transcript.

        Args:
            text: The user's message text.
        """
        if self._transcript is None:
            return
        with self._transcript:
            ui.Label(f"You: {text}", word_wrap=True, style=_USER_STYLE, height=0)

    def append_assistant_text(self, text: str) -> None:
        """Append assistant text, starting a new bubble or extending the current one.

        Args:
            text: The assistant text delta to append.
        """
        if self._transcript is None:
            return
        if self._current_assistant is None:
            # Start a fresh bubble; accumulate deltas in a list rather than reading
            # back and re-concatenating the label's full text on every chunk (that
            # read-modify-write copies the whole accumulated string each time —
            # O(n^2) over a long response).
            self._assistant_chunks = [text]
            with self._transcript:
                self._current_assistant = ui.Label(f"Agent: {text}", word_wrap=True, style=_ASSISTANT_STYLE, height=0)
        else:
            self._assistant_chunks.append(text)
            self._current_assistant.text = "Agent: " + "".join(self._assistant_chunks)

    def add_tool_row(self, tool_id: str, name: str, tool_input: dict) -> None:
        """Append a compact row describing a tool call.

        Args:
            tool_id: The tool-use id (used to match a later result).
            name: The tool name (e.g. ``Bash``).
            tool_input: The tool's input payload; its ``command``/``file_path``
                is shown as a short detail.
        """
        if self._transcript is None:
            return
        # Keep the displayed command compact; full input is in the agent's logs.
        with self._transcript:
            ui.Label(
                _tool_label(name, tool_input),
                word_wrap=True,
                style=_TOOL_STYLE,
                height=0,
            )
        # The assistant may emit more text after a tool call — start a fresh bubble.
        self._current_assistant = None

    def attach_tool_result(self, tool_use_id: str, text: str, is_error: bool) -> None:
        """Append a compact tool-result line to the transcript.

        Args:
            tool_use_id: The id of the tool call this result belongs to.
            text: The tool's output; only the first line (truncated) is shown.
            is_error: Whether the tool reported an error.
        """
        if self._transcript is None:
            return
        marker = "[err]" if is_error else "[ok]"
        snippet = _result_snippet(text)
        with self._transcript:
            ui.Label(f"   {marker} {snippet}", word_wrap=True, style=_TOOL_RESULT_STYLE, height=0)

    def finalize_turn(self, result_event: ResultEvent) -> None:
        """Mark the turn finished and show its final status and cost.

        Args:
            result_event: The terminal event for the turn.
        """
        self.set_busy(False)
        self.set_status(_done_status(getattr(result_event, "cost_usd", None)))
        self._current_assistant = None

    def show_error(self, message: str) -> None:
        """Render an error line in the transcript and reset the panel to idle.

        Args:
            message: The error message to display.
        """
        if self._transcript is not None:
            with self._transcript:
                ui.Label(f"[!] {message}", word_wrap=True, style=_ERROR_STYLE, height=0)
        self.set_busy(False)
        self.set_status("Error.")

    def scroll_to_bottom(self) -> None:
        """Pin the transcript to the latest message.

        Call one frame after content is added so the scroll extent reflects the
        new layout.
        """
        if self._scroll is not None:
            self._scroll.scroll_y = self._scroll.scroll_y_max
