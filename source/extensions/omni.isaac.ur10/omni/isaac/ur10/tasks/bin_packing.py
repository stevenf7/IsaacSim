# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.ur10 import UR10
import numpy as np
from omni.isaac.core.utils.stage import add_usd_reference
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.core.utils.rotations import euler_angles_to_quat
import carb
from omni.isaac.core.prims import XFormPrim, RigidPrim
import random


class BinPacking(BaseTask):
    def __init__(self) -> None:
        """[summary]
        """
        self.my_ur10 = None
        self.packing_bin = None
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._ur10_asset_path = nucleus_server + "/Isaac/Samples/Leonardo/Stage/ur10_bin_filling.usd"
        self._screw_asset_paths = [
            nucleus_server + "/Isaac/Props/Flip_Stack/large_corner_bracket_physics.usd",
            nucleus_server + "/Isaac/Props/Flip_Stack/screw_95_physics.usd",
            nucleus_server + "/Isaac/Props/Flip_Stack/screw_99_physics.usd",
            nucleus_server + "/Isaac/Props/Flip_Stack/small_corner_bracket_physics.usd",
            nucleus_server + "/Isaac/Props/Flip_Stack/t_connector_physics.usd",
        ]
        self._screws = []
        self._max_screws = 20
        self._screws_to_add = 0
        self._pipe_position = np.array([0, 0.85, 1.2])
        return

    def get_current_num_of_screws_to_add(self):
        return self._screws_to_add

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        # TODO: change values with USD
        super().set_up_scene(scene)
        add_usd_reference(usd_path=self._ur10_asset_path, prim_path="/World/Scene")
        self.my_ur10 = scene.add(
            UR10(stage=scene.stage, prim_path="/World/Scene/ur10", name="my_ur10", end_effector_prim_name="ee_link")
        )
        # TODO: change values with USD
        self.packing_bin = scene.add(
            RigidPrim(
                prim=scene.stage.GetPrimAtPath("/World/Scene/bin"),
                name="packing_bin",
                position=np.array([0.35, 0.15, -0.44]) * 100,
                orientation=euler_angles_to_quat(np.array([0, 0, 0])),
            )
        )
        # TODO: change values with USD
        self.my_ur10.set_gripper_length(length=19)
        # TODO: change values with USD
        self.my_ur10.add_surface_gripper(
            translate=self.my_ur10.gripper_length, direction="x", force_limit=5.0e20, torque_limit=5.0e20
        )
        return

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self.my_ur10.get_joints_state()
        bin_position, bin_orientation = self.packing_bin.get_pose()
        end_effector_position, _ = self.my_ur10.get_end_effector_pose()
        # TODO: change values with USD
        return {
            "packing_bin": {
                "position": bin_position,
                "orientation": bin_orientation,
                "target_position": np.array([0, 0.70, -0.44]) * 100,
                "size": np.array([0.25, 0.35, 0.20]) * 100,
            },
            "my_ur10": {"joint_positions": joints_state.positions, "end_effector_pose": end_effector_position},
        }

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        self.my_ur10.update_gripper()
        if self._screws_to_add > 0 and len(self._screws) < self._max_screws and control_index % 100 == 0:
            self._add_screw()
        return

    def reset(self):
        self._screws_to_add = 0
        self._screws = []
        return

    def add_screws(self, screws_number=10):
        self._screws_to_add += screws_number
        return

    def _add_screw(self):
        asset_path = self._screw_asset_paths[random.randint(0, len(self._screw_asset_paths) - 1)]
        prim_path = "/World/objects/object_{}".format(len(self._screws))
        prim = add_usd_reference(usd_path=asset_path, prim_path=prim_path)
        # TODO: change values with USD
        # TODO: deal with nested rigid body apis?
        self._screws.append(
            XFormPrim(prim=prim, name="screw_{}".format(len(self._screws)), position=100 * self._pipe_position)
        )
        self._screws_to_add -= 1
        return

    def cleanup(self) -> None:
        for i in range(len(self._screws)):
            self.scene.remove_object(self._screws[i].name)
            self._screws = []
        return
