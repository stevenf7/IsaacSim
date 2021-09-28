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
from omni.isaac.core.utils.types import RigidPrimState, DynamicState
from pxr import Gf, UsdPhysics, Usd
import numpy as np
from omni.isaac.dynamic_control import _dynamic_control


class RigidPrim(XFormPrim):
    def __init__(
        self,
        prim: Usd.Prim,
        name: str,
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
        super().__init__(prim, name=name, position=position, orientation=orientation, visible=visible)
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            print("has rigid body api")
            self._rigid_api = UsdPhysics.RigidBodyAPI(self._prim)
        else:
            self._rigid_api = UsdPhysics.RigidBodyAPI.Apply(self._prim)
        if prim.HasAPI(UsdPhysics.MassAPI):
            self._mass_api = UsdPhysics.MassAPI(self._prim)
        else:
            self._mass_api = UsdPhysics.MassAPI.Apply(self._prim)
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        # TODO: look at utils.setRigidBody(prim, "convexDecomposition", False)
        self.enable_usd_physics(True)
        if linear_velocity is not None:
            self.set_usd_linear_velocity(linear_velocity)
        if angular_velocity is not None:
            self.set_usd_angular_velocity(angular_velocity)
        if mass is not None:
            self.set_usd_mass(mass)
        mass = self.get_usd_mass()
        linear_velocity = self.get_usd_linear_velocity()
        angular_velocity = self.get_usd_angular_velocity()
        self._default_state = RigidPrimState(
            self._default_state.position, self._default_state.orientation, linear_velocity, angular_velocity, mass
        )
        self._handle = None
        return

    # TODO: check which space is it in
    def set_usd_linear_velocity(self, linear_velocity: np.ndarray) -> None:
        """Sets the linear velocity of the prim in stage. The method does this through the USD API.

        Args:
            linear_velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
        """
        linear_velocity = linear_velocity.tolist()
        linear_velocity = Gf.Vec3f(linear_velocity)
        # TODO: check if this attribute needs to be checked before or so
        self._rigid_api.CreateVelocityAttr().Set(linear_velocity)
        return

    # TODO: check which space is it in
    def set_usd_angular_velocity(self, angular_velocity: np.ndarray) -> None:
        """Sets the angular velocity of the prim in stage. The method does this through the USD API.

        Args:
            angular_velocity (np.ndarray): angular velocity to set the rigid prim to. Shape (3,).
        """
        angular_velocity = angular_velocity.tolist()
        angular_velocity = Gf.Vec3f(angular_velocity)
        self._rigid_api.CreateAngularVelocityAttr().Set(angular_velocity)
        return

    def get_usd_linear_velocity(self) -> np.ndarray:
        """
        Returns:
            np.ndarray: linear velocity of the rigid prim. Shape (3,).
        """
        return np.array(self._rigid_api.GetVelocityAttr().Get())

    def get_usd_angular_velocity(self) -> np.ndarray:
        """
        Returns:
            np.ndarray: angular velocity of the rigid prim. Shape (3,).
        """
        return np.array(self._rigid_api.GetAngularVelocityAttr().Get())

    # TODO: check which space is it in
    def set_angular_velocity(self, angular_velocity: np.ndarray) -> None:
        """Sets the angular velocity of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
            angular_velocity (np.ndarray): angular velocity to set the rigid prim to. Shape (3,).
        """
        self._dc_interface.set_rigid_body_angular_velocity(self._handle, angular_velocity)
        return

    def get_linear_velocity(self) -> np.ndarray:
        """
        Note: It has to be called while simulating i.e after .play() or .reset() is called

        Returns:
            np.ndarray: linear velocity of the rigid prim. Shape (3,).
        """
        return self._dc_interface.get_rigid_body_linear_velocity(self._handle)

    def get_angular_velocity(self) -> np.ndarray:
        """
        Note: It has to be called while simulating i.e after .play() or .reset() is called

        Returns:
            np.ndarray: angular velocity of the rigid prim. Shape (3,).
        """
        return self._dc_interface.get_rigid_body_angular_velocity(self._handle)

    def set_linear_velocity(self, linear_velocity: np.ndarray):
        """Sets the linear velocity of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
            linear_velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
        """
        self._dc_interface.set_rigid_body_linear_velocity(self._handle, linear_velocity)
        return

    def set_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """Sets the pose of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
             position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
             orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim. 
                                              quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
        """
        current_position, current_orientation = self.get_pose()
        if position is None:
            position = current_position
        if orientation is None:
            orientation = current_orientation
        pose = _dynamic_control.Transform(position, orientation)
        self._dc_interface.set_rigid_body_pose(self._handle, pose)
        return

    def get_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Gets the current pose of the prim. Note: It has to be called while simulating i.e after .play() or .reset() is called
        
        Returns:
            Tuple(np.ndarray, np.ndarray): the first position (3,) is the usd position and the second is the orientation 
                                            as a quaternion. quaternion is scalar-first (w, x, y, z). shape (4,).
        """
        pose = self._dc_interface.get_rigid_body_pose(self._handle)
        return np.asarray(pose.p), np.asarray(pose.r)

    def set_usd_mass(self, mass: float) -> None:
        """[summary]

        Args:
            mass (float): [description]
        """
        self._mass_api.CreateMassAttr(mass)
        return

    def get_usd_mass(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        self._mass_api.GetMassAttr()
        return

    def enable_usd_physics(self, flag: bool) -> None:
        """[summary]

        Args:
            flag (bool): [description]
        """
        self._rigid_api.CreateRigidBodyEnabledAttr(flag)
        return

    def enable_usd_kinematic(self, flag: bool) -> None:
        """[summary]

        Args:
            flag (bool): [description]
        """
        self._rigid_api.CreateKinematicEnabledAttr(flag)
        return

    def _initialize_handles(self) -> None:
        """[summary]
        """
        self._handle = self._dc_interface.get_rigid_body(self.prim_path)
        return

    def set_default_state(
        self,
        position: np.ndarray,
        orientation: np.ndarray,
        linear_velocity: np.ndarray,
        angular_velocity: np.ndarray,
        mass: float,
    ) -> None:
        """Sets the default state of the prim, that will be used with each reset. 

        Args:
            position (np.ndarray): [description]
            orientation (np.ndarray): [description]
            linear_velocity (np.ndarray): [description]
            angular_velocity (np.ndarray): [description]
            mass (float): [description]
        """
        self._default_state = RigidPrimState(position, orientation, linear_velocity, angular_velocity, mass)
        return

    def reset(self) -> None:
        """Resets the prim to its default state.
        """
        super().reset()
        self.set_angular_velocity(self._default_state.angular_velocity)
        self.set_linear_velocity(self._default_state.linear_velocity)
        self.set_usd_mass(self._default_state.mass)
        return

    def get_dynamic_state(self) -> None:
        """[summary]

        Returns:
            [type]: [description]
        """
        position, orientation = self.get_pose()
        return DynamicState(
            position=position,
            orientation=orientation,
            linear_velocity=self.get_linear_velocity(),
            angular_velocity=self.get_angular_velocity(),
        )
