# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.universal_robots import UR10
import numpy as np
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.rotations import euler_angles_to_quat
import carb
from omni.isaac.core.prims import XFormPrim, RigidPrim
import random


class BinFilling(BaseTask):
    def __init__(self, name="bin_filling", offset=None) -> None:
        """[summary]
        """
        BaseTask.__init__(self, name=name, offset=offset)
        self._ur10_robot = None
        self._packing_bin = None
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
        self._max_screws = 100
        self._screws_to_add = 0
        self._pipe_position = np.array([0, 0.85, 1.2])
        self._target_position = np.array([0, 0.90, -0.44]) / get_stage_units()
        self._bin_initial_position = np.array([0.35, 0.15, -0.44]) / get_stage_units()
        self._bin_size = np.array([0.25, 0.35, 0.20]) / get_stage_units()
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

        add_reference_to_stage(usd_path=self._ur10_asset_path, prim_path="/World/Scene")
        self._ur10_robot = scene.add(
            UR10(prim_path="/World/Scene/ur10", name="my_ur10", gripper_usd=None, attach_gripper=True)
        )
        self._ur10_robot.gripper.set_translate(value=16.2)
        self._ur10_robot.gripper.set_direction(value="x")
        self._ur10_robot.gripper.set_force_limit(value=1.0e6)
        self._ur10_robot.gripper.set_torque_limit(value=1.0e6)
        self._packing_bin = scene.add(
            RigidPrim(
                prim_path="/World/Scene/bin",
                name="packing_bin",
                position=self._bin_initial_position,
                orientation=euler_angles_to_quat(np.array([0, 0, np.pi / 2])),
            )
        )
        return

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self._ur10_robot.get_joints_state()
        bin_position, bin_orientation = self._packing_bin.get_world_pose()
        end_effector_position, end_effector_orientation = self._ur10_robot.end_effector.get_world_pose()
        # TODO: change values with USD
        return {
            "packing_bin": {
                "position": bin_position,
                "orientation": bin_orientation,
                "target_position": self._target_position,
                "size": self._bin_size,
            },
            "my_ur10": {
                "joint_positions": joints_state.positions,
                "end_effector_position": end_effector_position,
                "end_effector_orientation": end_effector_orientation,
            },
        }

    def pre_step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        BaseTask.pre_step(self, control_index=control_index, simulation_time=simulation_time)
        self._ur10_robot.gripper.update()
        if self._screws_to_add > 0 and len(self._screws) < self._max_screws and control_index % 50 == 0:
            self._add_screw()
        return

    def post_reset(self):
        self._screws_to_add = 0
        self._screws = []
        return

    def add_screws(self, screws_number=10):
        self._screws_to_add += screws_number
        return

    def _add_screw(self):
        asset_path = self._screw_asset_paths[random.randint(0, len(self._screw_asset_paths) - 1)]
        prim_path = "/World/objects/object_{}".format(len(self._screws))
        add_reference_to_stage(usd_path=asset_path, prim_path=prim_path)
        self._screws.append(
            self.scene.add(
                XFormPrim(
                    prim_path=prim_path, name="screw_{}".format(len(self._screws)), position=100 * self._pipe_position
                )
            )
        )
        self._screws_to_add -= 1
        return

    def cleanup(self) -> None:
        for i in range(len(self._screws)):
            self.scene.remove_object(self._screws[i].name)
            self._screws = []
        return

    def set_params(self, *args, **kwargs):
        raise NotImplementedError

    def get_params(self):
        params_representation = dict()
        params_representation["bin_name"] = {"value": self._packing_bin.name, "modifiable": False}
        params_representation["robot_name"] = {"value": self._ur10_robot.name, "modifiable": False}
        return params_representation

    def calculate_metrics(self) -> None:
        """[summary]
        """
        raise NotImplementedError

    def is_done(self) -> None:
        """[summary]
        """
        raise NotImplementedError
