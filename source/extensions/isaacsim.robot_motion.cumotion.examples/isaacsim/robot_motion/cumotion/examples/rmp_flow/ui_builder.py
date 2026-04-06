# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""UI builder for the Franka RMP-Flow motion planning example."""


import asyncio
from typing import Any

import omni.kit.app
import omni.timeline
import omni.ui as ui
from isaacsim.core.experimental.utils import stage as stage_utils
from isaacsim.core.rendering_manager import RenderingManager, ViewportManager
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.gui.components.element_wrappers import Button, CollapsableFrame, StateButton
from isaacsim.gui.components.style import get_style
from pxr import UsdPhysics

from .scenario import FrankaRmpFlowExample


class UIBuilder:
    """A UI builder class that creates and manages the user interface for the Franka RMP-Flow motion planning example.

    This class constructs a comprehensive UI with world controls and scenario management capabilities. It provides
    buttons for loading scenes, resetting scenarios, and running motion planning demonstrations. The interface handles
    asynchronous scene loading, physics initialization, and timeline control for the Franka robot motion planning
    example.

    The UI includes two main sections:
    - World Controls: Load and Reset buttons for scene management
    - Run Scenario: State button for starting and stopping the motion planning demonstration

    The class automatically handles timeline events, physics steps, and stage events to maintain proper state
    synchronization between the UI and the underlying simulation.
    """

    def __init__(self) -> None:
        # Frames are sub-windows that can contain multiple UI elements
        self.frames = []
        # UI elements created using a UIElementWrapper instance
        self.wrapped_ui_elements = []

        # Get access to the timeline to control stop/pause/play programmatically
        self._timeline = omni.timeline.get_timeline_interface()

        # Run initialization for the provided example
        self._on_init()

    ###################################################################################
    #           The Functions Below Are Called Automatically By extension.py
    ###################################################################################

    def on_menu_callback(self) -> None:
        """Handle menu callback when the UI is opened from the toolbar.

        This is called directly after build_ui().
        """

    def on_timeline_event(self, event: Any) -> None:
        """Handle timeline events such as play, pause, or stop.

        Args:
            event: Timeline event.

        """
        self._scenario_state_btn.reset()
        self._scenario_state_btn.enabled = False

    def on_physics_step(self, step: float) -> None:
        """Handle physics step callbacks during simulation.

        Physics steps only occur when the timeline is playing.

        Args:
            step: Size of physics step.

        """

    def on_stage_event(self, event: Any) -> None:
        """Handle stage events such as opening or closing a stage.

        Args:
            event: Stage event.

        """
        # If the user opens a new stage, the extension should completely reset
        self._reset_extension()

    def cleanup(self) -> None:
        """Clean up active callback functions when the stage is closed or extension is hot reloaded.

        Perform any necessary cleanup such as removing active callback functions.
        """
        for ui_elem in self.wrapped_ui_elements:
            ui_elem.cleanup()

    def build_ui(self) -> None:
        """Build a custom UI tool to run your extension.

        This function will be called any time the UI window is closed and reopened.
        """
        world_controls_frame = CollapsableFrame("World Controls", collapsed=False)

        with world_controls_frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                self._load_btn = Button(
                    "Load Button",
                    "LOAD",
                    tooltip="Load the scene and initialize the scenario",
                    on_click_fn=self._on_load_btn,
                )
                self.wrapped_ui_elements.append(self._load_btn)

                self._reset_btn = Button(
                    "Reset Button", "RESET", tooltip="Reset the scenario", on_click_fn=self._on_reset_btn
                )
                self._reset_btn.enabled = False
                self.wrapped_ui_elements.append(self._reset_btn)

        run_scenario_frame = CollapsableFrame("Run Scenario")

        with run_scenario_frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                self._scenario_state_btn = StateButton(
                    "Run Scenario",
                    "RUN",
                    "STOP",
                    on_a_click_fn=self._on_run_scenario_a_text,
                    on_b_click_fn=self._on_run_scenario_b_text,
                    physics_callback_fn=self._update_scenario,
                )
                self._scenario_state_btn.enabled = False
                self.wrapped_ui_elements.append(self._scenario_state_btn)

    ######################################################################################
    # Functions Below This Point Support The Provided Example
    ######################################################################################

    def _on_init(self) -> None:
        """Initialize the UI."""
        self._scenario = FrankaRmpFlowExample()

    def _on_load_btn(self) -> None:
        """Handle Load button click - loads scene and initializes scenario."""
        asyncio.ensure_future(self._load_scene_async())

    async def _load_scene_async(self) -> None:
        """Load the scene asynchronously without using World."""
        # Create new stage
        await stage_utils.create_new_stage_async(template="default stage")

        # Set up stage properties
        stage_utils.set_stage_up_axis("Z")
        stage_utils.set_stage_units(meters_per_unit=1.0)

        # Setup scene (load assets)
        await self._scenario.load_example_assets()

        # Set camera view
        ViewportManager.set_camera_view(camera="/OmniverseKit_Persp", eye=[2, 1.5, 2], target=[0, 0, 0])

        # Create physics scene if it doesn't exist
        stage = stage_utils.get_current_stage()
        physics_scene_path = "/World/PhysicsScene"
        if not stage.GetPrimAtPath(physics_scene_path).IsValid():
            UsdPhysics.Scene.Define(stage, physics_scene_path)
        await omni.kit.app.get_app().next_update_async()

        # Initialize physics if needed
        if SimulationManager.get_physics_sim_view() is None:
            SimulationManager.initialize_physics()

        # Play timeline to initialize physics tensors
        self._timeline.play()
        # Wait for multiple updates to ensure physics runs and tensors are initialized
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        # Setup scenario (post-load callback)
        self._setup_scenario()

    def _setup_scenario(self) -> None:
        """Initialize the scenario after assets are loaded.

        The user may assume that their assets have been loaded, that
        their objects are properly initialized, and that the timeline is paused on timestep 0.
        """
        self._scenario.setup()

        # UI management
        self._scenario_state_btn.reset()
        self._scenario_state_btn.enabled = True
        self._reset_btn.enabled = True

    def _on_reset_btn(self) -> None:
        """Handle Reset button click - resets the scenario."""
        asyncio.ensure_future(self._reset_scene_async())

    async def _reset_scene_async(self) -> None:
        """Reset the scene asynchronously without using World."""
        # Stop timeline
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        # Reset scenario
        self._scenario.reset()
        await omni.kit.app.get_app().next_update_async()

        # Play timeline to re-initialize physics tensors
        self._timeline.play()
        # Wait for multiple updates to ensure physics runs and tensors are initialized
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        # UI management
        self._scenario_state_btn.reset()
        self._scenario_state_btn.enabled = True

    def _update_scenario(self, step: float, *args: Any, **kwargs: Any) -> None:
        """Update the scenario on each physics step.

        Attached to the Run Scenario StateButton as the physics_callback_fn argument.
        When the a_text "RUN" is pressed, a subscription is made to call this function on every physics step.
        When the b_text "STOP" is pressed, the physics callback is removed.

        Args:
            step: The dt of the current physics step.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        """
        # Check if physics tensors are valid before updating
        if self._scenario._articulation is not None:
            if not self._scenario._articulation.is_physics_tensor_entity_valid():
                return
        self._scenario.update(step)

    def _on_run_scenario_a_text(self) -> None:
        """Play the timeline when the Run Scenario StateButton is clicked with a_text "RUN"."""
        self._timeline.play()

    def _on_run_scenario_b_text(self) -> None:
        """Pause the timeline when the Run Scenario StateButton is clicked with b_text "STOP"."""
        self._timeline.pause()

    def _reset_extension(self) -> None:
        """Reset all state when the user opens a new stage from self.on_stage_event().

        All state should be reset.
        """
        self._on_init()
        self._reset_ui()

    def _reset_ui(self) -> None:
        """Reset all UI elements to their default disabled state."""
        self._scenario_state_btn.reset()
        self._scenario_state_btn.enabled = False
        self._reset_btn.enabled = False
