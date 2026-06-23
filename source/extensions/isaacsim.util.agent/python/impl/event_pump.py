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

"""Marshal agent events from the reader thread onto the Kit main thread.

The :class:`~.agent_session.AgentSession` reader thread calls :meth:`on_event`
(thread-safe enqueue only). A per-frame subscription on the app update stream
drains the queue on the main thread and dispatches to the window — so omni.ui is
only ever touched from the main thread.
"""

from __future__ import annotations

import queue
from typing import TYPE_CHECKING

import carb.events
import omni.kit.app

from .stream_events import AssistantText, ErrorEvent, InitEvent, ResultEvent, StreamEvent, ToolResult, ToolUse

if TYPE_CHECKING:
    from .chat_window import ChatWindow


class EventPump:
    """Thread-safe queue + per-frame drain that dispatches events to the window.

    Args:
        window: The chat window that renders dispatched events on the main thread.
    """

    def __init__(self, window: ChatWindow) -> None:
        self._window = window
        self._queue: queue.Queue = queue.Queue()
        self._sub = None
        self._pending_scroll = False

    def on_event(self, event: StreamEvent) -> None:
        """Enqueue an event. Safe to call from any thread (the reader thread).

        Args:
            event: The parsed event to dispatch on the next frame.
        """
        self._queue.put(event)

    def start(self) -> None:
        """Begin draining the queue once per frame on the main thread."""
        if self._sub is None:
            self._sub = (
                omni.kit.app.get_app()
                .get_update_event_stream()
                .create_subscription_to_pop(self._drain, name="isaacsim.util.agent.event_pump")
            )

    def stop(self) -> None:
        """Stop draining and drop any pending events."""
        self._sub = None
        self._queue = queue.Queue()

    def discard_pending(self) -> None:
        """Drop queued events not yet dispatched, without stopping the drain.

        Used when the user stops a turn: events already enqueued (but not yet
        rendered) for the stopped turn should not flow to the window — e.g. a
        late ``result`` overwriting the "Stopped." status.
        """
        self._queue = queue.Queue()
        self._pending_scroll = False

    def _drain(self, _event: carb.events.IEvent) -> None:
        # Scroll requested by the previous frame's content now that layout settled.
        if self._pending_scroll:
            self._pending_scroll = False
            if self._window is not None:
                self._window.scroll_to_bottom()
        dispatched = False
        while True:
            try:
                event = self._queue.get_nowait()
            except queue.Empty:
                break
            self._dispatch(event)
            dispatched = True
        # New content this frame -> scroll on the next frame (extent is updated by then).
        if dispatched:
            self._pending_scroll = True

    def _dispatch(self, event: StreamEvent) -> None:
        window = self._window
        if window is None:
            return
        if isinstance(event, AssistantText):
            window.append_assistant_text(event.text)
        elif isinstance(event, ToolUse):
            window.add_tool_row(event.id, event.name, event.input)
        elif isinstance(event, ToolResult):
            window.attach_tool_result(event.tool_use_id, event.text, event.is_error)
        elif isinstance(event, ResultEvent):
            window.finalize_turn(event)
        elif isinstance(event, ErrorEvent):
            window.show_error(event.message)
        elif isinstance(event, InitEvent):
            pass  # session_id is captured inside AgentSession; nothing to render
        # UnknownEvent is intentionally ignored in the UI.
