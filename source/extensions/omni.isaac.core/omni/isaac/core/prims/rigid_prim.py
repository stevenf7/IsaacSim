# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.types import DynamicState
from omni.isaac.core.utils.prims import get_prim_at_path
from pxr import Gf, UsdPhysics
import numpy as np
from omni.isaac.dynamic_control import _dynamic_control


class RigidPrim(XFormPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "rigid_prim",
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        visible: bool = True,
        mass: Optional[float] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
    ) -> None:
        """Provides common functionalities to rigid prims such as cube, sphere..etc.

        Args:
            stage (Usd.Stage): current usd stage used.
            prim (Usd.Prim): prim object to encapsulate.
            geom (UsdGeom.Gprim): USD geometry object to encapsulate. You can retrive it using UsdGeom.Gprim(prim).
            name (str, optional): name given to the prim, this can be different than the prim path. Defaults to None.
            position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
            orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim. 
                                              quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
            mass (float, optional): mass of the rigid prim in kg. Defaults to None.
            linear_velocity (np.ndarray, optional): initial linear velocity of the rigid prim. Shape (3, ). Defaults to None.
            angular_velocity (np.ndarray, optional): initial angular velocity of the rigid prim. Shape (3, ). Defaults to None.
            visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
        """
        prim = get_prim_at_path(prim_path)
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._handle = None
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            self._rigid_api = UsdPhysics.RigidBodyAPI(prim)
        else:
            self._rigid_api = UsdPhysics.RigidBodyAPI.Apply(prim)
        if prim.HasAPI(UsdPhysics.MassAPI):
            self._mass_api = UsdPhysics.MassAPI(prim)
        else:
            self._mass_api = UsdPhysics.MassAPI.Apply(prim)
        XFormPrim.__init__(
            self, prim_path=prim_path, name=name, position=position, orientation=orientation, visible=visible
        )
        self._rigid_api.CreateRigidBodyEnabledAttr(True)
        if linear_velocity is not None:
            RigidPrim.set_linear_velocity(self, linear_velocity)
        if angular_velocity is not None:
            RigidPrim.set_angular_velocity(self, angular_velocity)
        if mass is not None:
            RigidPrim.set_mass(self, mass)
        linear_velocity = RigidPrim.get_linear_velocity(self)
        angular_velocity = RigidPrim.get_angular_velocity(self)
        self._default_state = DynamicState(
            self._default_state.position, self._default_state.orientation, linear_velocity, angular_velocity
        )
        return

    def set_linear_velocity(self, linear_velocity: np.ndarray):
        """Sets the linear velocity of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
            linear_velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_linear_velocity(self._handle, linear_velocity)
        else:
            self._rigid_api.GetVelocityAttr().Set(Gf.Vec3f(linear_velocity.tolist()))
        return

    def get_linear_velocity(self) -> np.ndarray:
        if self._handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_linear_velocity(self._handle)
        else:
            return np.array(self._rigid_api.GetVelocityAttr().Get())

    def set_angular_velocity(self, angular_velocity: np.ndarray) -> None:
        if self._handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_angular_velocity(self._handle, angular_velocity)
        else:
            self._rigid_api.GetAngularVelocityAttr().Set(Gf.Vec3f(angular_velocity.tolist()))
        return

    def get_angular_velocity(self):
        if self._handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_angular_velocity(self._handle)
        else:
            return np.array(self._rigid_api.GetAngularVelocityAttr().Get())

    def set_world_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """Sets the pose of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
             position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
             orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim. 
                                              quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            current_position, current_orientation = self.get_pose()
            if position is None:
                position = current_position
            if orientation is None:
                orientation = current_orientation
            pose = _dynamic_control.Transform(position, orientation)
            self._dc_interface.set_rigid_body_pose(self._handle, pose)
        else:
            XFormPrim.set_world_pose(self, position=position, orientation=orientation)
        return

    def get_world_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Gets the current pose of the prim. Note: It has to be called while simulating i.e after .play() or .reset() is called
        
        Returns:
            Tuple(np.ndarray, np.ndarray): the first position (3,) is the usd position and the second is the orientation 
                                            as a quaternion. quaternion is scalar-first (w, x, y, z). shape (4,).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            pose = self._dc_interface.get_rigid_body_pose(self._handle)
            return np.asarray(pose.p), np.asarray(pose.r)
        else:
            return XFormPrim.get_world_pose(self)

    def set_local_pose(self, translation=None, orientation=None):
        if self._handle is not None and self._dc_interface.is_simulating():
            raise NotImplementedError
        else:
            return XFormPrim.set_local_pose(translation=translation, orientation=orientation)

    def get_local_pose(self):
        if self._handle is not None and self._dc_interface.is_simulating():
            raise NotImplementedError
        else:
            return XFormPrim.get_local_pose()

    def set_mass(self, mass: float) -> None:
        """[summary]

        Args:
            mass (float): [description]
        """
        self._mass_api.GetMassAttr().Set(mass)
        return

    def get_mass(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self._mass_api.GetMassAttr().Get()

    def initialize_handles(self) -> None:
        """[summary]
        """
        self._handle = self._dc_interface.get_rigid_body(self.prim_path)
        return

    def set_default_state(
        self,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
    ) -> None:
        """Sets the default state of the prim, that will be used with each reset. 

        Args:
            position (np.ndarray): [description]
            orientation (np.ndarray): [description]
            linear_velocity (np.ndarray): [description]
            angular_velocity (np.ndarray): [description]
            mass (float): [description]
        """
        if position is not None:
            self._default_state.position = position
        if orientation is not None:
            self._default_state.orientation = orientation
        if linear_velocity is not None:
            self._default_state.linear_velocity = linear_velocity
        if angular_velocity is not None:
            self._default_state.angular_velocity = angular_velocity
        return

    def reset(self) -> None:
        """Resets the prim to its default state.
        """
        XFormPrim.reset(self)
        RigidPrim.set_angular_velocity(self, self._default_state.angular_velocity)
        RigidPrim.set_linear_velocity(self, self._default_state.linear_velocity)
        return

    def get_current_dynamic_state(self) -> None:
        """[summary]

        Returns:
            [type]: [description]
        """
        position, orientation = self.get_world_pose()
        return DynamicState(
            position=position,
            orientation=orientation,
            linear_velocity=self.get_linear_velocity(),
            angular_velocity=self.get_angular_velocity(),
        )
