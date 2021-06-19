# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import carb
from pxr import UsdGeom, Gf, UsdPhysics, Sdf, UsdLux
import omni.ext
import omni.usd
import omni.kit.settings

import asyncio
from omni.isaac.dynamic_control import _dynamic_control
import omni.physx as _physx

from omni.physx.scripts.physicsUtils import add_ground_plane
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.utils.scripts.scene_utils import set_translate, set_up_z_axis, setup_physics

import os
import numpy as np


def create_prim_from_usd(stage, prim_env_path, prim_usd_path, location):
    envPrim = stage.DefinePrim(prim_env_path, "Xform")  # create an empty Xform at the given path
    envPrim.GetReferences().AddReference(prim_usd_path)  # attach the USD to the given path
    set_translate(envPrim, location)  # set pose


class Replay:
    def __init__(self):
        self._timeline = omni.timeline.get_timeline_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self.created = False
        self._save_dir = None
        self._replay_data = False
        self._replay_count = 0
        self.traj_lengths = 0
        self._reset = False
        self._ar = _dynamic_control.INVALID_HANDLE

    def create_robot(self):
        """ load robot from USD
        """

        self._stage = omni.usd.get_context().get_stage()
        self._ar = _dynamic_control.INVALID_HANDLE

        ## unit conversions: RMP is in meters, kit is by default in cm
        self._meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)
        self._units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(self._stage)

        set_up_z_axis(self._stage)
        add_ground_plane(self._stage, "/physics/groundPlane", "Z", 1000.0, Gf.Vec3f(0.0), Gf.Vec3f(1.0))
        setup_physics(self._stage)

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        asset_path = nucleus_server + "/Isaac"
        robot_usd = asset_path + "/Robots/Franka/franka.usd"
        robot_path = "/scene/robot"
        create_prim_from_usd(self._stage, robot_path, robot_usd, Gf.Vec3d(0, 0, 0))

        # self._physxIFace.release_physics_objects()
        # self._physxIFace.force_load_physics_from_usd()

        light_prim = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/World/defaultLight"))
        light_prim.CreateIntensityAttr(500)

        self.created = True

    def step(self, step):
        """This function is called every timestep in the editor
        
        Arguments:
            step (float): elapsed time between steps
        """

        if self.created and self._timeline.is_playing():
            if self._reset:
                if self._ar == _dynamic_control.INVALID_HANDLE:
                    self._ar = self._dc.get_articulation("/scene/robot")
                home_joint_pos = [0.0, -1.30, 0.0, -2.83, 0.0, 2.03, 0.75, 0.0, 0.0]
                self._dc.wake_up_articulation(self._ar)
                self._dc.set_articulation_dof_position_targets(self._ar, home_joint_pos)
                self._replay_data = False
                self._replay_count = 0
                arrived = self.arrival_check(home_joint_pos)
                if arrived:
                    self._reset = False

            if self._replay_data:
                if self._replay_count < self.traj_lengths:
                    self._dc.wake_up_articulation(self._ar)
                    self._dc.set_articulation_dof_position_targets(
                        self._ar, self.joint_positions[self._replay_count, :].tolist()
                    )
                    self._replay_count += 1
                else:
                    self._replay_data = False
                    print("Replay Complete")
                    self._replay_count = 0

    def arrival_check(self, target_pos):
        current_dof = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_POS)
        current_pos = current_dof["pos"]
        arrived = np.allclose(np.array(target_pos), np.array(current_pos), rtol=1e2)
        return arrived

    def save_dir(self, dir_name):
        self._save_dir = dir_name

    def replay_data(self):
        if not self._replay_data:
            self._replay_data = True
            filename = self._save_dir
            # check if file exist
            if not os.path.exists(filename):
                carb.log_warn(f"filename {filename} doesn't exist")
                self._replay_data = False
            else:
                print("file used: ", filename)
                with open(filename, "r") as f:
                    traj_dict = eval(f.read())

                self.joint_positions = np.array(traj_dict["joint state"])
                self.traj_lengths = np.shape(self.joint_positions)[0]
                if self._ar == _dynamic_control.INVALID_HANDLE:
                    self._ar = self._dc.get_articulation("/scene/robot")
                self._replay_count = 0

        else:
            self._replay_data = False
            self._replay_count = 0

    def stop_tasks(self):
        self.created = False
        self._replay_count = 0
        self._replay_data = False
        self._reset = False

    def reset(self):
        self._ar = _dynamic_control.INVALID_HANDLE
        self._reset = True
