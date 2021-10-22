# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple
from omni.isaac.core.utils.nucleus import find_nucleus_server
import carb
import numpy as np
from omni.isaac.core.robots.robot import Robot
from omni.isaac.core.prims.rigid_prim import RigidPrim

# TODO: change import for surface gripper?
from omni.isaac.surface_gripper._surface_gripper import Surface_Gripper
from omni.isaac.surface_gripper._surface_gripper import Surface_Gripper_Properties
from omni.isaac.core.prims import XFormPrim
from omni.isaac.dynamic_control import _dynamic_control
from pxr import Usd


class UR10(Robot):
    def __init__(
        self,
        stage: Usd.Stage,
        prim_path: str,
        name: str,
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        end_effector_prim_name: Optional[str] = None,
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
        self._stage = stage
        prim = stage.GetPrimAtPath(prim_path)
        self._end_effector_prim_name = end_effector_prim_name
        if not prim.IsValid():
            prim = stage.DefinePrim(prim_path, "Xform")
            if usd_path:
                prim.GetReferences().AddReference(usd_path)
            else:
                result, nucleus_server = find_nucleus_server()
                if result is False:
                    carb.log_error("Could not find nucleus server with /Isaac folder")
                    return
                asset_path = nucleus_server + "/Isaac/Robots/UR10/ur10.usd"
                prim.GetReferences().AddReference(asset_path)
                self._end_effector_prim_name = "ee_link"
        super().__init__(prim=prim, name=name, position=position, orientation=orientation, articulation_controller=None)
        self._end_effector = None
        self._virtual_gripper_props = None
        self._virtual_gripper = None
        self._gripper = None
        self._gripper_prim_name = None
        self._gripper_length = 0
        # TODO: check the default state and how to reset
        return

    @property
    def end_effector(self) -> RigidPrim:
        """[summary]

        Returns:
            RigidPrim: [description]
        """
        # TODO: need to account for the gripper here
        return self._end_effector

    @property
    def virtual_gripper(self):
        return self._virtual_gripper

    @property
    def virtual_gripper_properties(self):
        return self._virtual_gripper_props

    @property
    def gripper(self):
        return self._gripper

    @property
    def gripper_length(self):
        return self._gripper_length

    def get_end_effector_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """[summary]

        Returns:
            Tuple[np.ndarray, np.ndarray]: [description]
        """
        # TODO: need to account for the gripper here
        return self._end_effector.get_pose()

    def get_end_effector_linear_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        # TODO: need to account for the gripper here
        return self._end_effector.get_linear_velocity()

    def get_end_effector_angular_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        # TODO: need to account for the gripper here
        return self._end_effector.get_angular_velocity()

    def set_gripper_length(self, length: float):
        self._gripper_length = length
        return

    def initialize_handles(self) -> None:
        """[summary]
        """
        super().initialize_handles()
        self._end_effector_handle = self._dc_interface.find_articulation_body(
            self._handle, self._end_effector_prim_name
        )
        end_effector_prim_path = self._dc_interface.get_rigid_body_path(self._end_effector_handle)
        end_effector_prim = self._stage.GetPrimAtPath(end_effector_prim_path)
        self._end_effector = RigidPrim(prim=end_effector_prim, name=self._name + "_end_effector")
        self._end_effector.initialize_handles()
        # TODO: ask about gravity
        self.disable_gravity()
        return

    def reset(self) -> None:
        """[summary]
        """
        super().reset()
        self.set_joint_positions(np.array([-np.pi / 2, -np.pi / 2, -np.pi / 2, -np.pi / 2, np.pi / 2, 0]))
        return

    def add_surface_gripper(
        self,
        translate,
        direction,
        grip_threshold=1,
        force_limit=5.0e5,
        torque_limit=5.0e5,
        bend_angle=np.pi / 24,
        kp=1.0e5,
        kd=1.0e4,
    ) -> None:
        # TODO: change default values to meters when usd changes
        if self._virtual_gripper is None:
            virtual_gripper_props = Surface_Gripper_Properties()
            virtual_gripper_props.parentPath = self.prim_path + "/" + self._end_effector_prim_name
            virtual_gripper_props.d6JointPath = virtual_gripper_props.parentPath + "/d6FixedJoint"
            virtual_gripper_props.gripThreshold = grip_threshold
            virtual_gripper_props.forceLimit = force_limit
            virtual_gripper_props.torqueLimit = torque_limit
            virtual_gripper_props.bendAngle = bend_angle
            virtual_gripper_props.stiffness = kp
            virtual_gripper_props.damping = kd
            virtual_gripper_props.disableGravity = True
            tr = _dynamic_control.Transform()
            if direction == "x":
                tr.p.x = translate
            elif direction == "y":
                tr.p.y = translate
            elif direction == "x":
                tr.p.z = translate
            else:
                carb.log_error("Direction specified for the surface gripper doesn't exist")
            virtual_gripper_props.offset = tr
            self._virtual_gripper_props = virtual_gripper_props
            virtual_gripper = Surface_Gripper(self._dc_interface)
            virtual_gripper.initialize(virtual_gripper_props)
            self._virtual_gripper = virtual_gripper
        return

    def close_gripper(self):
        if self.virtual_gripper is not None:
            return self.virtual_gripper.close()
        else:
            raise NotImplementedError

    def open_gripper(self):
        if self.virtual_gripper is not None:
            return self.virtual_gripper.open()
        else:
            raise NotImplementedError

    def update_gripper(self):
        if self.virtual_gripper is not None:
            self.virtual_gripper.update()
        else:
            raise NotImplementedError

    def is_gripper_closed(self):
        if self.virtual_gripper is not None:
            return self.virtual_gripper.is_closed()
        else:
            raise NotImplementedError

    # TODO: add support to long gripper as well
    def add_gripper(self, usd_path=None):
        # TODO: account for relative pose here..etc to account for the gripper pose
        self._gripper_prim_name = self.prim_path + "/" + self._end_effector_prim_name
        if usd_path is None:
            gripper_prim = self._stage.GetPrimAtPath(self._gripper_prim_name)
            result, nucleus_server = find_nucleus_server()
            if result is False:
                carb.log_error("Could not find nucleus server with /Isaac folder")
                return
            asset_path = nucleus_server + "/Isaac/Robots/UR10/Props/short_gripper.usd"
            gripper_prim.GetReferences().AddReference(asset_path)
            self._gripper = XFormPrim(prim=self._stage.GetPrimAtPath(self._gripper_prim_name), name="gripper")
            # TODO: change values with USD
            self._gripper_length = 16.11
            self.add_surface_gripper(translate=self._gripper_length, direction="x")
        else:
            gripper_prim = self._stage.DefinePrim(self._gripper_prim_name, "Xform")
            gripper_prim.GetReferences().AddReference(usd_path)
            # self._gripper = XFormPrim(prim=gripper_prim, name="gripper")
            # TODO: self._add_suction_gripper(x_translate=17)
        return
