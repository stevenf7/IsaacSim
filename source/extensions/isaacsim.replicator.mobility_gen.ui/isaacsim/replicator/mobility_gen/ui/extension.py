# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Extension for generating mobility data using teleoperated robots in Omniverse."""


import asyncio
import datetime
import glob
import os
import tempfile

import carb
import isaacsim.core.experimental.utils.app as app_utils

# import examples to register example robots / scenarios
import isaacsim.replicator.mobility_gen.examples  # noqa: F401
import omni.ext
import omni.kit
import omni.kit.usdz_export as usdz_export
import omni.ui as ui
from isaacsim.core.experimental.objects import GroundPlane
from isaacsim.core.experimental.utils.stage import open_stage, save_stage
from isaacsim.core.rendering_manager import ViewportManager
from isaacsim.core.simulation_manager import SimulationEvent, SimulationManager
from isaacsim.replicator.experimental.mobility_gen import (
    ROBOTS,
    SCENARIOS,
    Config,
    GamepadDriver,
    KeyboardDriver,
    MobilityGenScenario,
    MobilityGenWriter,
    OccupancyMap,
)

if "MOBILITY_GEN_DATA" in os.environ:
    DATA_DIR = os.environ["MOBILITY_GEN_DATA"]
else:
    DATA_DIR = os.path.expanduser("~/MobilityGenData")

RECORDINGS_DIR = os.path.join(DATA_DIR, "recordings")
SCENARIOS_DIR = os.path.join(DATA_DIR, "scenarios")


class MobilityGenExtension(omni.ext.IExt):
    """Extension for generating mobility data using teleoperated robots in Omniverse.

    This extension provides a user interface for configuring and running mobility generation scenarios.
    Users can select robot types, scenario types, and occupancy maps to create teleoperated data collection
    sessions. The extension handles stage loading, robot spawning, camera setup, and data recording for
    machine learning training datasets.

    The extension creates two windows:
    - MobilityGen: Main control panel for scenario configuration and recording management
    - MobilityGen - Occupancy Map: Visualization window showing the occupancy map with robot position

    Key features include:
    - Support for multiple robot types and scenario configurations
    - Real-time occupancy map visualization with robot tracking
    - Keyboard and gamepad input support for teleoperation
    - Automatic data recording with timestamped output files
    - Stage caching and management for consistent scenario replay
    - Physics-based simulation with configurable time steps
    """

    def on_startup(self, ext_id: str):
        """Initialize the MobilityGen extension.

        Sets up keyboard and gamepad drivers, UI windows for occupancy map visualization and teleop controls,
        and initializes recording state.

        Args:
            ext_id: Extension identifier.
        """
        self.keyboard = KeyboardDriver.connect()
        self.gamepad = GamepadDriver.connect()
        self.scenario: MobilityGenScenario = None
        self.config: Config = None

        self.count = 0

        self.scenario_path: str | None = None
        self.cached_stage_path: str | None = None

        self.writer: MobilityGenWriter | None = None
        self._physics_callback_id: int | None = None
        self.step: int = 0
        self.is_recording: bool = False
        self.recording_enabled: bool = False
        self.recording_time: float = 0.0

        self._occupancy_map_image_provider = omni.ui.ByteImageProvider()

        self._visualize_window = omni.ui.Window("MobilityGen - Occupancy Map", width=300, height=300)
        with self._visualize_window.frame:
            self._occ_map_frame = ui.Frame()
            self._occ_map_frame.set_build_fn(self.build_occ_map_frame)

        self._teleop_window = omni.ui.Window("MobilityGen", width=300, height=300)

        with self._teleop_window.frame:
            with ui.VStack():
                with ui.VStack():
                    with ui.HStack():
                        ui.Label("Stage")
                        self.scene_usd_field_string_model = ui.SimpleStringModel()
                        self.scene_usd_field = ui.StringField(model=self.scene_usd_field_string_model, height=25)

                    with ui.HStack():
                        ui.Label("Occupancy Map")
                        self.omap_field_string_model = ui.SimpleStringModel()
                        self.omap_field = ui.StringField(model=self.omap_field_string_model, height=25)

                    with ui.HStack():
                        ui.Label("Robot Type")
                        self.robot_combo_box = ui.ComboBox(0, *ROBOTS.names())

                    with ui.HStack():
                        ui.Label("Scenario Type")
                        self.scenario_combo_box = ui.ComboBox(0, *SCENARIOS.names())

                    ui.Button("Build", clicked_fn=self.build_scenario)
                    # ui.Button("Build", clicked_fn=self.build_scenario)

                with ui.VStack():
                    self.recording_count_label = ui.Label("")
                    self.recording_dir_label = ui.Label(f"Output directory: {RECORDINGS_DIR}")
                    self.recording_name_label = ui.Label("")
                    self.recording_step_label = ui.Label("")

                    ui.Button("Reset", clicked_fn=self.reset)
                    with ui.HStack():
                        ui.Button("Start Recording", clicked_fn=self.enable_recording)
                        ui.Button("Stop Recording", clicked_fn=self.disable_recording)

        self.update_recording_count()
        self.clear_recording()

        self._occupancy_map_is_not_yaml_msg = (
            "Occupancy map must be a YAML file.  Please enter a file path with a valid YAML extension."
        )
        self._occupancy_map_invalid_path_no_yaml_ext_dialog = omni.kit.window.popup_dialog.MessageDialog(
            message=self._occupancy_map_is_not_yaml_msg,
            title="Invalid occupancy map.",
            disable_cancel_button=True,
            ok_handler=lambda dialog: dialog.hide(),
        )

        self._occupancy_map_doesnt_exist_msg = "Occupancy map does not exist.  Please enter a file path that exists."
        self._occupancy_map_invalid_path_does_not_exist = omni.kit.window.popup_dialog.MessageDialog(
            message=self._occupancy_map_doesnt_exist_msg,
            disable_cancel_button=True,
            title="Invalid occupancy map.",
            ok_handler=lambda dialog: dialog.hide(),
        )

    def build_occ_map_frame(self):
        """Build the occupancy map visualization frame.

        Creates an image widget to display the occupancy map visualization if a scenario is active.
        """
        if self.scenario is not None:
            with ui.VStack():
                image_widget = ui.ImageWithProvider(self._occupancy_map_image_provider)

    def draw_visualization_image(self):
        """Update the occupancy map visualization image.

        Retrieves the current visualization image from the scenario and updates the image provider for display
        in the UI.
        """
        if self.scenario is not None:
            image = self.scenario.get_visualization_image().copy().convert("RGBA")
            data = list(image.tobytes())
            self._occupancy_map_image_provider.set_bytes_data(data, [image.width, image.height])
            self._occ_map_frame.rebuild()

    def update_recording_count(self):
        """Update the recording count display.

        Counts the number of existing recordings in the recordings directory and updates the UI label.
        """
        num_recordings = len(glob.glob(os.path.join(RECORDINGS_DIR, "*")))
        self.recording_count_label.text = f"Number of recordings: {num_recordings}"

    def create_config(self) -> Config:
        """Create a configuration object from current UI settings.

        Returns:
            A Config object with the selected scenario type, robot type, and scene USD path.
        """
        config = Config(
            scenario_type=list(SCENARIOS.names())[
                self.scenario_combo_box.model.get_item_value_model().get_value_as_int()
            ],
            robot_type=list(ROBOTS.names())[self.robot_combo_box.model.get_item_value_model().get_value_as_int()],
            scene_usd=self.scene_usd_field_string_model.as_string,
        )
        return config

    def scenario_type(self):
        """Get the currently selected scenario type.

        Returns:
            The scenario type class corresponding to the current combo box selection.
        """
        index = self.scenario_combo_box.model.get_item_value_model().get_value_as_int()
        return SCENARIOS.get_index(index)

    def on_shutdown(self):
        """Clean up resources when the extension shuts down.

        Disconnects input drivers and removes physics callbacks from the world.
        """
        self.keyboard.disconnect()
        self.gamepad.disconnect()
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None

    def start_new_recording(self):
        """Start a new recording session.

        Creates a timestamped recording directory, initializes the writer with config and occupancy map data,
        and resets recording state.
        """
        recording_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        recording_path = os.path.join(RECORDINGS_DIR, recording_name)
        writer = MobilityGenWriter(recording_path)
        writer.write_config(self.config)
        writer.write_occupancy_map(self.scenario.occupancy_map)
        writer.copy_stage(self.cached_stage_path)
        self.step = 0
        self.recording_time = 0.0
        self.recording_name_label.text = f"Current recording name: {recording_name}"
        self.recording_step_label.text = f"Current recording duration: {self.recording_time:.2f}s"
        self.writer = writer
        self.update_recording_count()

    def clear_recording(self):
        """Clear the current recording session.

        Resets the writer and clears recording display labels.
        """
        self.writer = None
        self.recording_name_label.text = "Current recording name: "
        self.recording_step_label.text = "Current recording duration: "

    def clear_scenario(self):
        """Clear the current scenario.

        Resets the scenario instance and cached stage path.
        """
        self.scenario = None
        self.cached_stage_path = None

    def enable_recording(self):
        """Enable data recording for the current scenario.

        Starts a new recording session if a scenario is active and recording is not already enabled.
        """
        if not self.recording_enabled:
            if self.scenario is not None:
                self.start_new_recording()
            self.recording_enabled = True

    def disable_recording(self):
        """Disable data recording and clear the current recording session."""
        self.recording_enabled = False
        self.clear_recording()

    def reset(self):
        """Reset the scenario to its initial state.

        Clears the current recording writer, resets the scenario, and starts a new recording if recording is enabled.
        """
        self.writer = None
        self.scenario.reset()
        if self.recording_enabled:
            self.start_new_recording()
        self.draw_visualization_image()

    def on_physics(self, step_size: int, context=None):
        """Physics step callback that advances the scenario and handles recording.

        Args:
            step_size: The physics step size in simulation time units.
            context: Optional simulation context passed by the simulation manager.
        """
        if self.scenario is not None:

            is_alive = self.scenario.step(step_size)

            if not is_alive:
                self.reset()

            if self.writer is not None:
                state_dict = self.scenario.state_dict_common()
                self.writer.write_state_dict_common(state_dict, step=self.step)
                self.step += 1
                self.recording_time += step_size
                if self.step % 15 == 0:
                    self.recording_step_label.text = f"Current recording duration: {self.recording_time:.2f}s"

    def _check_occupancy_map_yaml_path(self) -> bool:
        """Validate the occupancy map YAML file path from the UI field.

        Returns:
            True if the path exists and has a valid YAML extension, False otherwise.
        """
        occupancy_map_yaml_path = os.path.expanduser(self.omap_field_string_model.as_string)

        if not os.path.exists(occupancy_map_yaml_path):
            carb.log_warn(self._occupancy_map_doesnt_exist_msg)
            self._occupancy_map_invalid_path_does_not_exist.show()

            return False

        _, file_ext = os.path.splitext(os.path.basename(occupancy_map_yaml_path))

        if file_ext.lower() not in [".yaml", ".yml"]:
            carb.log_warn(self._occupancy_map_is_not_yaml_msg)
            self._occupancy_map_invalid_path_no_yaml_ext_dialog.show()
            return False

        return True

    def build_scenario(self):
        """Build and initialize a new mobility generation scenario based on UI parameters.

        Asynchronously creates a scenario using the selected robot type, scenario type, stage file, and occupancy map.
        """

        async def _build_scenario_async():

            self.clear_recording()
            self.clear_scenario()
            self.disable_recording()

            # Get parameters from UI
            scenario_type_str = list(SCENARIOS.names())[
                self.scenario_combo_box.model.get_item_value_model().get_value_as_int()
            ]
            robot_type_str = list(ROBOTS.names())[self.robot_combo_box.model.get_item_value_model().get_value_as_int()]
            scene_usd_str = self.scene_usd_field_string_model.as_string

            robot_type = ROBOTS.get(robot_type_str)
            scenario_type = SCENARIOS.get(scenario_type_str)

            # Set config
            self.config = Config(scenario_type=scenario_type_str, robot_type=robot_type_str, scene_usd=scene_usd_str)

            if self._check_occupancy_map_yaml_path():
                occupancy_map = OccupancyMap.from_ros_yaml(os.path.expanduser(self.omap_field_string_model.as_string))
            else:
                return

            # Open stage and save local copy
            open_stage(scene_usd_str)
            # Check if stage is a USDZ file
            if scene_usd_str.endswith(".usdz"):
                self.cached_stage_path = os.path.join(tempfile.mkdtemp(), "stage.usdz")
                await usdz_export.usdz_export(scene_usd_str, self.cached_stage_path)
            else:
                self.cached_stage_path = os.path.join(tempfile.mkdtemp(), "stage.usd")
                save_stage(self.cached_stage_path)
                # Kit adds /Render/.../SDGPipeline prims to the live stage during viewport
                # rendering setup.  Strip them from the saved file using the standalone USD
                # API so they are never baked into recording stage copies — the replay script
                # would otherwise crash when it tries to remove them via Kit's stage API.
                from pxr import Usd as _Usd

                _disk_stage = _Usd.Stage.Open(self.cached_stage_path)
                for _sdg_path in (
                    "/Render/PostProcess/SDGPipeline",
                    "/Render/PostRender/SDGPipeline",
                    "/Render/Simulation/SDGPipeline",
                ):
                    if _disk_stage.GetPrimAtPath(_sdg_path).IsValid():
                        _disk_stage.RemovePrim(_sdg_path)
                _disk_stage.Save()
                del _disk_stage

            # Setup physics with the correct timestep
            SimulationManager.setup_simulation(dt=robot_type.physics_dt)

            # Add ground plane (physics only — hide mesh to prevent z-fighting
            # with the warehouse USD floor; template=None avoids a missing texture error)
            from isaacsim.core.experimental.utils.stage import get_current_stage as _get_stage
            from pxr import UsdGeom as _UsdGeom

            _gp = GroundPlane("/World/ground_plane", templates=None)
            _stage = _get_stage()
            for _mp in _gp.meshes.paths:
                _UsdGeom.Imageable(_stage.GetPrimAtPath(_mp)).MakeInvisible()

            # Add robot
            robot = robot_type.build("/World/robot")

            # Set the chase camera
            chase_camera_path = robot.build_chase_camera()
            if ViewportManager.get_viewport_api() is not None:
                ViewportManager.set_camera(chase_camera_path)

            # Set the scenario
            self.scenario = scenario_type.from_robot_occupancy_map(robot, occupancy_map)

            # Draw the occupancy map
            self.draw_visualization_image()

            # Start the simulation and initialize physics
            app_utils.play()
            await app_utils.update_app_async()
            SimulationManager.initialize_physics()

            # Register physics callback
            if self._physics_callback_id is not None:
                SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = SimulationManager.register_callback(
                self.on_physics, event=SimulationEvent.PHYSICS_POST_STEP
            )

            self.reset()

        asyncio.ensure_future(_build_scenario_async())
