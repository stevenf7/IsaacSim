# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse
import glob
import os
import re
from multiprocessing import Process

CUSTOM_APP_PATH = ""
try:
    from isaacsim import SimulationApp
except:
    # running in custom app env
    CUSTOM_APP_PATH = f"{os.environ['EXP_PATH']}/omni.agent_sdg.base.kit"
    from app_framework import SimulationApp

CONFIG = {"renderer": "RayTracedLighting", "headless": True, "width": 1920, "height": 1080}

"""
Standalone script to schedule people sdg jobs in a local env.
"""


class AgentSDG:
    def __init__(self, sim_app):
        import omni.anim.navigation.navmesh.recast as navmesh

        self.config_dict = None
        self._sim_manager = None
        self._data_generator = None
        self._settings = None
        self._sim_app = sim_app
        self._navmesh = navmesh.acquire_interface()
        self._nav_mesh_event_handle = None
        self.navmesh_baking_complete = False

    def set_config(self, config_file):
        import carb
        from omni.replicator.agent.core.data_generation import DataGeneration
        from omni.replicator.agent.core.simulation import SimulationManager

        self._sim_manager = SimulationManager()
        self.config_dict, is_modified = self._sim_manager.load_config_file(config_file)
        if not self.config_dict:
            carb.log_error("Loading config file ({0}) fails. Data generation will not start.".format(config_file))
            return

        camera_start_index = 0
        if "camera_start_index" in self.config_dict["global"]:
            camera_start_index = self.config_dict["global"]["camera_start_index"]
        lidar_start_index = 0
        if "lidar_start_index" in self.config_dict["global"]:
            lidar_start_index = self.config_dict["global"]["lidar_start_index"]
        self._data_generator = DataGeneration(self.config_dict, camera_start_index, lidar_start_index)

    def set_simulation_settings(self):
        import carb
        import omni.replicator.core as rep

        rep.settings.carb_settings("/omni/replicator/backend/writeThreads", 16)
        self._settings = carb.settings.get_settings()
        self._settings.set("/rtx/rtxsensor/coordinateFrameQuaternion", "0.5,-0.5,-0.5,-0.5")
        self._settings.set("/app/scripting/ignoreWarningDialog", True)
        self._settings.set("/persistent/exts/omni.anim.navigation.core/navMesh/viewNavMesh", False)
        self._settings.set("/exts/omni.anim.people/navigation_settings/navmesh_enabled", True)
        self._settings.set("/persistent/exts/omni.replicator.agent/aim_camera_to_character", True)
        self._settings.set("/persistent/exts/omni.replicator.agent/min_camera_distance", 6.5)
        self._settings.set("/persistent/exts/omni.replicator.agent/max_camera_distance", 14.5)
        self._settings.set("/persistent/exts/omni.replicator.agent/max_camera_look_down_angle", 60)
        self._settings.set("/persistent/exts/omni.replicator.agent/min_camera_look_down_angle", 0)
        self._settings.set("/persistent/exts/omni.replicator.agent/min_camera_height", 2)
        self._settings.set("/persistent/exts/omni.replicator.agent/max_camera_height", 3)
        self._settings.set("/persistent/exts/omni.replicator.agent/character_focus_height", 0.7)
        self._settings.set("/persistent/exts/omni.replicator.agent/frame_write_interval", 1)

    def bake_navmesh(self):
        import carb
        import omni.anim.navigation.core as nav

        _nav = nav.acquire_interface()
        # Do not proceed if navmesh volume does not exist
        if _nav.get_navmesh_volume_count() == 0:
            carb.log_error("Scene does not have navigation volume. Stopping data generation and closing app.")
            self._sim_app.update()
            self._sim_app.close()
            return

        _nav.start_navmesh_baking()

        def nav_mesh_callback(event):
            if event.type == nav.EVENT_TYPE_NAVMESH_READY:
                self._nav_mesh_event_handle = None
                self.navmesh_baking_complete = True
            elif event.type == nav.EVENT_TYPE_NAVMESH_BAKE_FAILED:
                carb.log_error("Navmesh baking failed. Stoping data generation and closing app.")
                self._nav_mesh_event_handle = None
                self._sim_app.update()
                self._sim_app.close()

        self._nav_mesh_event_handle = _nav.get_navmesh_event_stream().create_subscription_to_pop(nav_mesh_callback)

    def generate_data(self, config_file):
        import carb
        import omni.replicator.core as rep
        from isaacsim.core.api.utils.stage import open_stage

        # Set simulation settings
        self.set_simulation_settings()

        # Load from config file
        self.set_config(config_file)

        # Open stage with blocking call
        stage_open_result = open_stage(self.config_dict["scene"]["asset_path"])

        if not stage_open_result:
            carb.log_error("Unable to open stage {}".format(self.config_dict["scene"]["asset_path"]))
            self._sim_app.close()
        self._sim_app.update()

        # Start navmesh baking
        self.bake_navmesh()

        # Wait for navmesh baking to finish
        while self.navmesh_baking_complete != True:
            self._sim_app.update()

        # Create character and cameras
        self._sim_manager.load_agents_cameras_from_config_file()
        self._sim_app.update()

        # Create random character actions (when character section exists)
        if "character" in self.config_dict:
            commands_list = self._sim_manager.generate_random_commands()
            self._sim_manager.save_commands(commands_list)  # Write commands to file
            self._sim_app.update()

        if "robot" in self.config_dict:
            commands_list = self._sim_manager.generate_random_robot_commands()
            self._sim_manager.save_robot_commands(commands_list)  # Write commands to file
            self._sim_app.update()

        # Run data generation
        self._data_generator._init_recorder()
        skip_frames = self._settings.get("/persistent/exts/omni.replicator.agent/skip_starting_frames")
        for i in range(self._data_generator._num_frames + skip_frames):
            rep.orchestrator.step(pause_timeline=False)

        rep.orchestrator.stop()
        self._sim_app.update()

        # Clear State after completion
        self._data_generator._clear_recorder()
        self._sim_app.update()
        self._sim_app.close()


def enable_extensions():
    # Enable extensions
    from isaacsim.core.api.utils.extensions import enable_extension

    enable_extension("omni.kit.viewport.window")
    enable_extension("omni.kit.manipulator.prim")
    enable_extension("omni.kit.property.usd")
    enable_extension("omni.anim.timeline")
    enable_extension("omni.anim.graph.core")
    enable_extension("omni.anim.retarget.core")
    enable_extension("omni.kit.scripting")
    enable_extension("omni.extended.materials")
    enable_extension("omni.anim.people")
    enable_extension("omni.replicator.agent.core")
    enable_extension("omni.kit.mesh.raycast")


def launch_data_generation(config_file):

    # Initalize kit app
    kit = SimulationApp(launch_config=CONFIG, experience=CUSTOM_APP_PATH)

    # Enable extensions
    enable_extensions()
    kit.update()

    # Load modules from extensions
    import carb
    import omni.kit.loop._loop as omni_loop

    loop_runner = omni_loop.acquire_loop_interface()
    loop_runner.set_manual_step_size(1.0 / 30.0)
    loop_runner.set_manual_mode(True)
    carb.settings.get_settings().set("/app/player/useFixedTimeStepping", False)

    # set config app
    sdg = AgentSDG(kit)
    sdg.generate_data(config_file)


def get_args():
    parser = argparse.ArgumentParser("Agent SDG")
    parser.add_argument("-c", "--config_file", required=True, help="Path to config file or a folder of config files")
    args, _ = parser.parse_known_args()
    return args


def main():
    args = get_args()
    config_path = args.config_file

    # Check for config file or folder
    if os.path.isfile(config_path):
        launch_data_generation(config_path)
    else:
        print("Invalid config path passed. Path must be a file")


if __name__ == "__main__":
    main()
