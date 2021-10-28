# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional
import numpy as np
from omni.isaac.core.robots.robot import Robot
from omni.isaac.surface_gripper import SurfaceGripper
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.utils.prims import get_prim_at_path
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.utils.nucleus import find_nucleus_server
import carb


class UR10(Robot):
    def __init__(
        self,
        prim_path: str,
        name: str = "ur10_robot",
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        end_effector_prim_name: Optional[str] = None,
        attach_gripper=False,
        gripper_usd="default",
    ) -> None:
        """[summary]

        Args:
            stage (Usd.Stage): [description]
            prim_path (str): [description]
            name (str): [description]
            usd_path (str, optional): [description]
            position (Optional[np.ndarray], optional): [description]. Defaults to None.
            orientation (Optional[np.ndarray], optional): [description]. Defaults to None.
        """
        prim = get_prim_at_path(prim_path)
        self._end_effector = None
        self._gripper = None
        self._end_effector_prim_name = end_effector_prim_name
        if not prim.IsValid():
            if usd_path:
                add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
            else:
                result, nucleus_server = find_nucleus_server()
                if result is False:
                    carb.log_error("Could not find nucleus server with /Isaac folder")
                    return
                usd_path = nucleus_server + "/Isaac/Robots/UR10/ur10.usd"
                add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
                if self._end_effector_prim_name is None:
                    self._end_effector_prim_name = "ee_link"
        else:
            # TODO: change this
            if self._end_effector_prim_name is None:
                self._end_effector_prim_name = "ee_link"
        super().__init__(
            prim_path=prim_path, name=name, position=position, orientation=orientation, articulation_controller=None
        )
        if attach_gripper:
            if gripper_usd == "default":
                result, nucleus_server = find_nucleus_server()
                if result is False:
                    carb.log_error("Could not find nucleus server with /Isaac folder")
                    return
                gripper_usd = nucleus_server + "/Isaac/Robots/UR10/Props/short_gripper.usd"
                translate = 16.11
                direction = "x"
                self._gripper = SurfaceGripper(usd_path=gripper_usd, translate=translate, direction=direction)
            elif gripper_usd is None:
                carb.log_warn("Not adding a gripper usd, the gripper already exists in the ur10 asset")
                self._gripper = SurfaceGripper(usd_path=None)
            else:
                raise NotImplementedError
        self._attach_gripper = attach_gripper
        return

    @property
    def attach_gripper(self):
        return self._attach_gripper

    @property
    def end_effector(self) -> RigidPrim:
        """[summary]

        Returns:
            RigidPrim: [description]
        """
        return self._end_effector

    @property
    def gripper(self) -> RigidPrim:
        """[summary]

        Returns:
            RigidPrim: [description]
        """
        return self._gripper

    def initialize_handles(self) -> None:
        """[summary]
        """
        end_effector_prim_path = self.prim_path + "/" + self._end_effector_prim_name
        if self._attach_gripper:
            self._gripper.initialize_handles(root_prim_path=end_effector_prim_path)
        self._end_effector = RigidPrim(prim_path=end_effector_prim_path, name=self._name + "_end_effector")
        super().initialize_handles()
        self.disable_gravity()
        self._end_effector.initialize_handles()
        return

    def post_reset(self) -> None:
        """[summary]
        """
        super().post_reset()
        self.set_joint_positions(np.array([-np.pi / 2, -np.pi / 2, -np.pi / 2, -np.pi / 2, np.pi / 2, 0]))
        return
