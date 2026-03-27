# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


"""Extension for optimizing Isaac Sim performance through automatic rendering and loop management based on timeline state."""


import carb
import carb.eventdispatcher
import omni.ext
import omni.kit.app
import omni.timeline

ASYNC_TOGGLE_SETTING = "/exts/isaacsim.core.throttling/enable_async"
MANUAL_TOGGLE_SETTING = "/exts/isaacsim.core.throttling/enable_manualmode"


class Extension(omni.ext.IExt):
    """Extension class for the isaacsim.core.throttling extension.

    This extension automatically optimizes Isaac Sim performance by managing rendering settings based on
    timeline state. It provides two main throttling modes: async rendering toggle and manual loop mode.

    When async rendering toggle is enabled, the extension automatically disables async rendering during
    simulation playback to ensure deterministic behavior, then re-enables it with a frame delay after
    stopping or pausing. This helps balance performance and simulation accuracy.

    When manual loop mode is enabled, the extension takes control of the application loop during simulation,
    allowing for more precise timing control and improved performance in certain scenarios.

    Additionally, the extension manages eco mode and gizmo visibility, disabling them during simulation
    for better performance and re-enabling them when stopped or paused for improved visual feedback
    during scene editing.

    The extension responds to timeline events (play, stop, pause) to automatically adjust these settings,
    ensuring optimal performance during simulation while maintaining good usability during scene editing.
    """

    def on_startup(self, ext_id):
        """Initialize the throttling extension.

        Sets up timeline event subscriptions, frame counting for async rendering, and applies initial
        throttling settings based on configuration.

        Args:
            ext_id: The extension ID.
        """
        # Initialize loop runner
        self._loop_runner = None
        try:
            from omni.kit.loop import _loop as omni_loop

            self._loop_runner = omni_loop.acquire_loop_interface()
        except Exception:
            pass

        # frame counting for async toggle
        self._frame_count = 0
        self._waiting_for_async_reenable = False
        self._frame_update_subscription = None
        self._frame_delay = 10  # default 10 frame delay

        # Enable the developer throttling settings when extension starts
        carb.settings.get_settings().set("/app/show_developer_preference_section", True)

        self.timeline_event_sub_play = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.timeline.GLOBAL_EVENT_PLAY,
            on_event=self._on_play,
            observer_name="isaacsim.core.throttling.Extension._on_play",
        )
        self.timeline_event_sub_stop = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.timeline.GLOBAL_EVENT_STOP,
            on_event=self._on_stop,
            observer_name="isaacsim.core.throttling.Extension._on_stop",
        )
        self.timeline_event_sub_pause = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.timeline.GLOBAL_EVENT_PAUSE,
            on_event=self._on_pause,
            observer_name="isaacsim.core.throttling.Extension._on_pause",
        )

        _settings = carb.settings.get_settings()

        if _settings.get(ASYNC_TOGGLE_SETTING):
            # Enable async rendering at startup
            _settings.set("/app/asyncRendering", True)
            _settings.set("/app/asyncRenderingLowLatency", True)

        if _settings.get(MANUAL_TOGGLE_SETTING):
            self._set_loop_manual_mode(False)

    def _set_loop_manual_mode(self, manual_mode: bool):
        """Configure the loop runner's manual mode.

        Args:
            manual_mode: Whether to enable manual mode for the loop runner.
        """
        if self._loop_runner is not None:
            try:
                self._loop_runner.set_manual_mode(manual_mode)
            except Exception:
                pass

    def _on_frame_update(self, event: carb.events.IEvent):
        """Frame update callback for async toggle frame delay.

        Args:
            event: The frame update event.
        """
        if not self._waiting_for_async_reenable:
            return
        self._frame_count += 1

        if self._frame_count >= self._frame_delay:
            # Check timeline did not play within the frame delay
            timeline = omni.timeline.get_timeline_interface()
            if not timeline.is_playing():
                # toggle async rendering
                _settings = carb.settings.get_settings()
                if _settings.get(ASYNC_TOGGLE_SETTING):
                    _settings.set("/app/asyncRendering", True)
                    _settings.set("/app/asyncRenderingLowLatency", True)

            self._waiting_for_async_reenable = False
            self._frame_count = 0

            # Unsubscribe to save on frame update callback overhead
            if self._frame_update_subscription is not None:
                self._frame_update_subscription = None

    def _start_frame_counting(self):
        """Start counting frames for async rendering delay."""
        if self._waiting_for_async_reenable:
            return

        self._frame_count = 0
        self._waiting_for_async_reenable = True

        # Create subscription on-demand to save on overhead
        self._frame_update_subscription = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.kit.app.GLOBAL_EVENT_UPDATE,
            on_event=self._on_frame_update,
            observer_name="IsaacSimThrottling._on_frame_update",
        )

    def _on_play(self, event: carb.eventdispatcher.Event):
        """Timeline play event callback - disable eco mode and gizmos during runtime.

        Args:
            event: The timeline play event.
        """
        _settings = carb.settings.get_settings()
        _settings.set("/rtx/ecoMode/enabled", False)
        _settings.set("/exts/omni.kit.hydra_texture/gizmos/enabled", False)

        if _settings.get(ASYNC_TOGGLE_SETTING):
            _settings.set("/app/asyncRendering", False)
            _settings.set("/app/asyncRenderingLowLatency", False)

        if _settings.get(MANUAL_TOGGLE_SETTING):
            self._set_loop_manual_mode(True)

    def _on_stop(self, event: carb.eventdispatcher.Event):
        """Timeline stop event callback - enable eco mode and gizmos when stopped.

        Args:
            event: The timeline stop event.
        """
        _settings = carb.settings.get_settings()
        _settings.set("/rtx/ecoMode/enabled", True)
        _settings.set("/exts/omni.kit.hydra_texture/gizmos/enabled", True)

        if _settings.get(ASYNC_TOGGLE_SETTING):
            # Start frame delay counting to give replicator time to finish
            self._start_frame_counting()

        if _settings.get(MANUAL_TOGGLE_SETTING):
            self._set_loop_manual_mode(False)

    def _on_pause(self, event: carb.eventdispatcher.Event):
        """Timeline pause event callback - enable eco mode and gizmos when paused.

        Args:
            event: The timeline pause event.
        """
        _settings = carb.settings.get_settings()
        _settings.set("/rtx/ecoMode/enabled", True)
        _settings.set("/exts/omni.kit.hydra_texture/gizmos/enabled", True)

        if _settings.get(ASYNC_TOGGLE_SETTING):
            # Start frame delay counting to give replicator time to finish
            self._start_frame_counting()

        if _settings.get(MANUAL_TOGGLE_SETTING):
            self._set_loop_manual_mode(False)

    def on_shutdown(self):
        """Clean up the extension's resources.

        Unsubscribes from timeline events and frame update callbacks, and resets frame counting state.
        """
        self.timeline_event_sub_play = None
        self.timeline_event_sub_stop = None
        self.timeline_event_sub_pause = None

        if self._frame_update_subscription is not None:
            self._frame_update_subscription = None

        self._waiting_for_async_reenable = False
        self._frame_count = 0
