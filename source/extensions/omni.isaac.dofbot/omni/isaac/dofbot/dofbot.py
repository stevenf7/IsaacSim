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
from omni.isaac.core.articulations import ArticulationGripper
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.utils.prims import get_prim_at_path
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.stage import add_reference_to_stage
import carb


class DofBot(Robot):
    def __init__(
        self,
        prim_path: str,
        name: str = "dofbot_robot",
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        end_effector_prim_name: Optional[str] = None,
        gripper_dof_names=None,
        gripper_open_position=None,
        gripper_closed_position=None,
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
                usd_path = nucleus_server + "/Isaac/Robots/Dofbot/dofbot.usd"
                add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
                if self._end_effector_prim_name is None:
                    self._end_effector_prim_name = "Finger_Right_01"
                if gripper_dof_names is None:
                    gripper_dof_names = ["Finger_Left_01_RevoluteJoint", "Finger_Right_01_RevoluteJoint"]
                if gripper_open_position is None:
                    gripper_open_position = np.array([-0.67192185, 0.67192185])
                if gripper_closed_position is None:
                    gripper_closed_position = np.array([0.523599, -0.523599])
        else:
            # TODO: change this
            if self._end_effector_prim_name is None:
                self._end_effector_prim_name = "Finger_Right_01"
            if gripper_dof_names is None:
                gripper_dof_names = ["Finger_Left_01_RevoluteJoint", "Finger_Right_01_RevoluteJoint"]
            if gripper_open_position is None:
                gripper_open_position = np.array([-0.67192185, 0.67192185])
            if gripper_closed_position is None:
                gripper_closed_position = np.array([0.523599, -0.523599])
        super().__init__(
            prim_path=prim_path, name=name, position=position, orientation=orientation, articulation_controller=None
        )
        if gripper_dof_names is not None:
            self._gripper = ArticulationGripper(
                gripper_dof_names=gripper_dof_names,
                gripper_open_position=gripper_open_position,
                gripper_closed_position=gripper_closed_position,
            )
        return

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
        super().initialize_handles()
        self._end_effector_handle = self._dc_interface.find_articulation_body(
            self._handle, self._end_effector_prim_name
        )
        end_effector_prim_path = self._dc_interface.get_rigid_body_path(self._end_effector_handle)
        self._end_effector = RigidPrim(prim_path=end_effector_prim_path, name=self._name + "_end_effector")
        self._end_effector.initialize_handles()
        self.gripper.initialize_handles(
            root_prim_path=self.prim_path, articulation_controller=self._articulation_controller
        )
        return

    def reset(self) -> None:
        """[summary]
        """
        super().reset()
        self._articulation_controller.switch_dof_control_mode(dof_index=self.gripper.dof_indices[0], mode="position")
        self._articulation_controller.switch_dof_control_mode(dof_index=self.gripper.dof_indices[1], mode="position")
        return
