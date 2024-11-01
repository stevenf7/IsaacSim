# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


"""
Standalone script to run a people sdg job in a local env.

Usage:
    python sdg_scheduler.py -c default_config.yaml [-f sensor_placements.json] [--save_usd]
"""

import argparse
import os

import numpy as np

try:
    CUSTOM_APP_PATH = f"{os.environ['EXP_PATH']}/omni.agent_sdg.base.kit"
    if not os.path.exists(CUSTOM_APP_PATH):
        CUSTOM_APP_PATH = ""
        from isaacsim.simulation_app import SimulationApp
    else:
        raise
except:
    # try to import app_framework, we *might* be running in custom app env
    from app_framework import SimulationApp

APP_CONFIG = {"renderer": "RayTracedLighting", "headless": False, "width": 1920, "height": 1080}


class AgentSDG:
    def __init__(self, config_file_path, camera_file_path, save_usd):
        self.config_file_path = config_file_path
        self.camera_file_path = camera_file_path
        self.save_usd = save_usd
        self.camera_placements_json = None
        self._sim_app = None
        self._sim_manager = None
        self._setup_sim_sub = None
        self._dg_sub = None
        self._settings = None

    def run(self):
        # Start kit app
        self._sim_app = SimulationApp(launch_config=APP_CONFIG, experience=CUSTOM_APP_PATH)
        self._sim_app.update()
        # Enable all required extensions
        self._enable_extensions()
        # Set up global settings
        self._set_simulation_settings()
        # Set up simulation and start data generation
        self._setup_simulation_and_start_data_generation()
        # Wait for data generation finishes
        while self._dg_sub:
            self._sim_app.update()
        # [Optional] Save the scene
        if self.save_usd == True:
            try:
                import omni.client
                import omni.usd

                writer_selection = self._sim_manager.get_config_file_property_group("replicator", "writer_selection")
                params = writer_selection.content_prop.get_value()
                save_to_path = omni.client.combine_urls("{}/".format(params["output_dir"]), "scene.usd")
                omni.usd.get_context().save_as_stage(save_to_path)
                print("Save scene to: " + str(save_to_path))
                self._sim_app.update()
            except:
                print("Caught exception. Unable to save USD.")
        # Close app
        self._sim_app.close()

    def _enable_extensions(self):
        import omni.kit.app

        ext_manager = omni.kit.app.get_app().get_extension_manager()

        ext_manager.set_extension_enabled_immediate("omni.kit.viewport.window", True)
        ext_manager.set_extension_enabled_immediate("omni.kit.manipulator.prim", True)
        ext_manager.set_extension_enabled_immediate("omni.kit.property.usd", True)
        ext_manager.set_extension_enabled_immediate("omni.kit.scripting", True)
        ext_manager.set_extension_enabled_immediate("omni.anim.timeline", True)
        ext_manager.set_extension_enabled_immediate("omni.anim.graph.core", True)
        ext_manager.set_extension_enabled_immediate("omni.anim.retarget.core", True)
        ext_manager.set_extension_enabled_immediate("omni.anim.navigation.core", True)
        ext_manager.set_extension_enabled_immediate("omni.anim.navigation.recast", True)
        ext_manager.set_extension_enabled_immediate("omni.anim.people", True)
        ext_manager.set_extension_enabled_immediate("isaacsim.replicator.agent.core", True)
        ext_manager.set_extension_enabled_immediate("omni.kit.mesh.raycast", True)
        ext_manager.set_extension_enabled_immediate("omni.extended.materials", True)

        self._sim_app.update()

    def _set_simulation_settings(self):
        import carb
        import omni.replicator.core as rep

        rep.settings.carb_settings("/omni/replicator/backend/writeThreads", 16)
        self._settings = carb.settings.get_settings()
        self._settings.set("/rtx/rtxsensor/coordinateFrameQuaternion", "0.5,-0.5,-0.5,-0.5")
        self._settings.set("/app/scripting/ignoreWarningDialog", True)
        self._settings.set("/persistent/exts/omni.anim.navigation.core/navMesh/viewNavMesh", False)
        self._settings.set("/exts/omni.anim.people/navigation_settings/navmesh_enabled", True)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/aim_camera_to_character", True)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/min_camera_distance", 6.5)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/max_camera_distance", 14.5)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/max_camera_look_down_angle", 60)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/min_camera_look_down_angle", 0)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/min_camera_height", 2)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/max_camera_height", 3)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/character_focus_height", 0.7)
        self._settings.set("/persistent/exts/isaacsim.replicator.agent/frame_write_interval", 1)

    def _setup_simulation_and_start_data_generation(self):
        import carb
        from isaacsim.replicator.agent.core.simulation import SimulationManager

        self._sim_manager = SimulationManager()
        load_succeed = self._sim_manager.load_config_file(self.config_file_path)
        if not load_succeed:
            carb.log_error(
                "Loading config file ({0}) fails. Data generation will not start.".format(self.config_file_path)
            )
            return

        # [Optional] Update camera number by placement file
        if self.camera_file_path:
            self._read_camera_json()
            self.self._sim_manager.get_config_file()["global"]["camera_num"] = len(self.camera_placements_json)

        def setup_sim_callback(e):
            # [Optional] Update spawned cameras positions by placement file
            if self.camera_file_path:
                self._place_cameras()
            self._setup_sim_sub = None

        def generate_data_callback(e):
            self._dg_sub = None

        # Set up simulation and start data generation
        self._setup_sim_sub = self._sim_manager.register_set_up_simulation_done_callback(setup_sim_callback)
        self._dg_sub = self._sim_manager.register_data_generation_callback(generate_data_callback)
        self._sim_manager.set_up_simulation_from_config_file(
            will_generate_random_commands=True, will_run_data_generation=True
        )

    # ===== Camera placement related =====

    def _read_camera_json(self):
        import json

        import carb
        import omni.client

        # Read json file
        result, version, context = omni.client.read_file(self.camera_file_path)
        if result != omni.client.Result.OK:
            carb.log_error(f"Cannot load camera file path: {self.camera_file_path}. Skip camera placement.")
            return
        json_str = memoryview(context).tobytes().decode("utf-8")
        self.camera_placements_json = json.loads(json_str)

    def _place_cameras(self):
        import carb

        # Perform placement
        from isaacsim.replicator.agent.core.stage_util import CameraUtil

        camera_prims = CameraUtil.get_cameras_in_stage()
        count = 0
        for camera_dict in self.camera_placements_json:
            if count >= len(camera_prims):
                carb.log_warn("No enough cameras in the scene to set placement. Will skip the rest placement data.")
                break
            self._place_one_camera(camera_dict, camera_prims[count])
            count += 1

        print(f"Place total {count} cameras.")

    def _place_one_camera(self, camera_dict, camera_prim):
        from isaacsim.core.utils.rotations import euler_to_rot_matrix
        from isaacsim.replicator.agent.core.stage_util import CameraUtil
        from pxr import Gf

        # Extract focal length
        # - In OV, the default pixel size is 20.955/1920=0.0109140625mm
        ov_focal_length = camera_dict["focal_length"] * 0.0109140625
        # Extract transformation
        ov_pos = Gf.Vec3d(camera_dict["x"], camera_dict["y"], camera_dict["height"])
        yaw = camera_dict["yaw"]
        pitch = camera_dict["pitch"]
        np_mat_yaw = euler_to_rot_matrix(np.array([0, yaw, 0]), degrees=True, extrinsic=False)
        np_mat_pitch = euler_to_rot_matrix(np.array([-pitch, 0, 0]), degrees=True, extrinsic=False)
        np_mat_default = euler_to_rot_matrix(
            np.array([90, -90, 0]), degrees=True, extrinsic=False
        )  # To make sure when yaw=0, the camera in IsaacSim points to X positive
        rot_matrix = (
            Gf.Matrix3d(np_mat_pitch.T.tolist())
            * Gf.Matrix3d(np_mat_yaw.T.tolist())
            * Gf.Matrix3d(np_mat_default.T.tolist())
        )
        # ov_rot_euler = rot_matrix.ExtractRotation().Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
        ov_rot = rot_matrix.ExtractRotation().GetQuat()
        CameraUtil.set_camera(camera_prim, ov_pos, ov_rot, ov_focal_length)


def get_args():
    parser = argparse.ArgumentParser("Agent SDG")
    parser.add_argument("-c", "--config_file", required=True, help="Path to a ORA config file")
    parser.add_argument(
        "-f", "--camera_placement_json_file", required=False, help="Path to camera placement json file."
    )
    parser.add_argument(
        "--save_usd",
        action=argparse.BooleanOptionalAction,
        help="Save the simulated scene when data generation finishes.",
    )
    args, _ = parser.parse_known_args()
    return args


def main():
    # Read command line arguments
    args = get_args()
    config_file_path = args.config_file
    camera_file_path = args.camera_placement_json_file
    save_usd = args.save_usd
    # Check files exist
    if not os.path.isfile(config_file_path):
        print("Invalid config file path. Exit.")
        return
    if camera_file_path and not os.path.isfile(camera_file_path):
        print("Invalid camera placement path. Exit.")
        return
    # Start SDG
    sdg = AgentSDG(config_file_path, camera_file_path, save_usd)
    sdg.run()


if __name__ == "__main__":
    main()
