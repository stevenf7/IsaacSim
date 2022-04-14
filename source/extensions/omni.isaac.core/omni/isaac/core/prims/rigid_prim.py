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
from omni.isaac.core.utils.prims import get_prim_at_path, get_prim_parent
from omni.isaac.core.utils.transformations import tf_matrix_from_pose
from omni.isaac.core.utils.rotations import gf_quat_to_np_array
from pxr import Gf, UsdPhysics, Usd, UsdGeom
import numpy as np
from omni.isaac.dynamic_control import _dynamic_control
import carb


class RigidPrim(XFormPrim):
    """
            Provides high level functions to deal with a rigid body prim and its attributes/ properties.
            If there is an prim present at the path, it will use it. Otherwise, a new XForm prim at
            the specified prim path will be created.

            Notes: if the prim does not already have a rigid body api applied to it before init, it will apply it. 

        Args:
            prim_path (str): prim path of the Prim to encapsulate or create.
            name (str, optional): shortname to be used as a key by Scene class. 
                                  Note: needs to be unique if the object is added to the Scene. 
                                  Defaults to "rigid_prim".
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            translation (Optional[np.ndarray], optional): translation in the local frame of the prim
                                                          (with respect to its parent prim). shape is (3, ).
                                                          Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world/ local frame of the prim
                                                          (depends if translation or position is specified).
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
            scale (Optional[np.ndarray], optional): local scale to be applied to the prim's dimensions. shape is (3, ).
                                                    Defaults to None, which means left unchanged.
            visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
            mass (Optional[float], optional): mass in kg. Defaults to None.
            linear_velocity (Optional[np.ndarray], optional): linear velocity in the world frame. Defaults to None.
            angular_velocity (Optional[np.ndarray], optional): angular velocity in the world frame. Defaults to None.
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "rigid_prim",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
        mass: Optional[float] = None,
        density: Optional[float] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
    ) -> None:
        prim = get_prim_at_path(prim_path)
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._handle = None
        # TODO: check also the children and the parent if they have rigid body api
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            self._rigid_api = UsdPhysics.RigidBodyAPI(prim)
        else:
            self._rigid_api = UsdPhysics.RigidBodyAPI.Apply(prim)
        if prim.HasAPI(UsdPhysics.MassAPI):
            self._mass_api = UsdPhysics.MassAPI(prim)
        else:
            self._mass_api = UsdPhysics.MassAPI.Apply(prim)
        XFormPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            scale=scale,
            visible=visible,
        )
        self._rigid_api.CreateRigidBodyEnabledAttr(True)
        if linear_velocity is not None:
            RigidPrim.set_linear_velocity(self, linear_velocity)
        if angular_velocity is not None:
            RigidPrim.set_angular_velocity(self, angular_velocity)
        if mass is not None:
            RigidPrim.set_mass(self, mass)
        elif density is not None:
            RigidPrim.set_density(self, density)
        linear_velocity = RigidPrim.get_linear_velocity(self)
        angular_velocity = RigidPrim.get_angular_velocity(self)
        self._default_state = DynamicState(
            self._default_state.position, self._default_state.orientation, linear_velocity, angular_velocity
        )
        self._handles_initialized = False
        return

    @property
    def handles_initialized(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        return self._handles_initialized

    def set_linear_velocity(self, velocity: np.ndarray):
        """Sets the linear velocity of the prim in stage.

        Args:
            velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_linear_velocity(self._handle, velocity)
        else:
            self._rigid_api.GetVelocityAttr().Set(Gf.Vec3f(velocity.tolist()))
        return

    def get_linear_velocity(self) -> np.ndarray:
        """
        Returns:
            np.ndarray: current linear velocity of the the rigid prim. Shape (3,).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_linear_velocity(self._handle)
        else:
            return np.array(self._rigid_api.GetVelocityAttr().Get())

    def set_angular_velocity(self, velocity: np.ndarray) -> None:
        """Sets the angular velocity of the prim in stage.

        Args:
            velocity (np.ndarray): angular velocity to set the rigid prim to. Shape (3,).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_angular_velocity(self._handle, velocity)
        else:
            self._rigid_api.GetAngularVelocityAttr().Set(Gf.Vec3f(velocity.tolist()))
        return

    def get_angular_velocity(self):
        """
        Returns:
            np.ndarray: current angular velocity of the the rigid prim. Shape (3,).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_angular_velocity(self._handle)
        else:
            return np.array(self._rigid_api.GetAngularVelocityAttr().Get())

    def set_world_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """Sets prim's pose with respect to the world's frame.

        Args:
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            current_position, current_orientation = self.get_world_pose()
            if position is None:
                position = current_position
            if orientation is None:
                orientation = current_orientation
            pose = _dynamic_control.Transform(
                position, [orientation[1], orientation[2], orientation[3], orientation[0]]
            )
            self._dc_interface.set_rigid_body_pose(self._handle, pose)
        else:
            XFormPrim.set_world_pose(self, position=position, orientation=orientation)
        return

    def get_world_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the world's frame.

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the world frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the world frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            pose = self._dc_interface.get_rigid_body_pose(self._handle)
            return np.asarray(pose.p), np.asarray([pose.r[3], pose.r[0], pose.r[1], pose.r[2]])
        else:
            return XFormPrim.get_world_pose(self)

    def set_local_pose(
        self, translation: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None
    ) -> None:
        """Sets prim's pose with respect to the local frame (the prim's parent frame).

        Args:
            translation (Optional[np.ndarray], optional): translation in the local frame of the prim
                                                          (with respect to its parent prim). shape is (3, ).
                                                          Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            local_transform = tf_matrix_from_pose(translation=translation, orientation=orientation)
            parent_world_tf = UsdGeom.Xformable(get_prim_parent(self._prim)).ComputeLocalToWorldTransform(
                Usd.TimeCode.Default()
            )
            my_world_transform = np.matmul(parent_world_tf, local_transform)
            transform = Gf.Transform()
            transform.SetMatrix(Gf.Matrix4d(np.transpose(my_world_transform)))
            calculated_position = transform.GetTranslation()
            calculated_orientation = transform.GetRotation().GetQuat()
            RigidPrim.set_world_pose(
                self, position=np.array(calculated_position), orientation=gf_quat_to_np_array(calculated_orientation)
            )
            return
        else:
            XFormPrim.set_local_pose(self, translation=translation, orientation=orientation)
            return

    def get_local_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the local frame (the prim's parent frame).

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the local frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the local frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        if self._handle is not None and self._dc_interface.is_simulating():
            parent_world_tf = UsdGeom.Xformable(get_prim_parent(self._prim)).ComputeLocalToWorldTransform(
                Usd.TimeCode.Default()
            )
            world_position, world_orientation = RigidPrim.get_world_pose(self)
            my_world_transform = tf_matrix_from_pose(translation=world_position, orientation=world_orientation)
            local_transform = np.matmul(np.linalg.inv(np.transpose(parent_world_tf)), my_world_transform)
            transform = Gf.Transform()
            transform.SetMatrix(Gf.Matrix4d(np.transpose(local_transform)))
            calculated_translation = transform.GetTranslation()
            calculated_orientation = transform.GetRotation().GetQuat()
            return np.array(calculated_translation), gf_quat_to_np_array(calculated_orientation)
        else:
            return XFormPrim.get_local_pose(self)

    def set_mass(self, mass: float) -> None:
        """
        Args:
            mass (float): mass of the rigid body in kg.
        """
        self._mass_api.GetMassAttr().Set(mass)
        return

    def get_mass(self) -> float:
        """
        Returns:
            float: mass of the rigid body in kg.
        """
        return self._mass_api.GetMassAttr().Get()

    def set_density(self, density: float) -> None:
        """
        Args:
            mass (float): density of the rigid body.
        """
        self._mass_api.GetDensityAttr().Set(density)
        return

    def get_density(self) -> float:
        """
        Returns:
            float: density of the rigid body.
        """
        return self._mass_api.GetDensityAttr().Get()

    def enable_rigid_body_physics(self) -> None:
        """ enable rigid body physics (enabled by default):
            Object will be moved by external forces such as gravity and collisions
        """
        self._rigid_api.GetRigidBodyEnabledAttr().Set(True)
        return

    def disable_rigid_body_physics(self) -> None:
        """ disable rigid body physics (enabled by default):
            Object will not be moved by external forces such as gravity and collisions
        """
        self._rigid_api.GetRigidBodyEnabledAttr().Set(False)
        return

    def initialize(self) -> None:
        """initilaizes dynamic control/ physX handles.
           If the object is added to a scene before the first world reset, handles will be initialized.
        """
        if self._handles_initialized:
            return
        self._handles_initialized = True
        carb.log_info("initializing handles for {}".format(self.prim_path))
        self._handle = self._dc_interface.get_rigid_body(self.prim_path)
        return

    def set_default_state(
        self,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
    ) -> None:
        """Sets the default state of the prim, that will be used after each reset. 

        Args:
            position (np.ndarray): position in the world frame of the prim. shape is (3, ).
                                   Defaults to None, which means left unchanged.
            orientation (np.ndarray): quaternion orientation in the world frame of the prim. 
                                      quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                      Defaults to None, which means left unchanged.
            linear_velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
            angular_velocity (np.ndarray): angular velocity to set the rigid prim to. Shape (3,).
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

    def get_default_state(self) -> DynamicState:
        """
        Returns:
            DynamicState: returns the default state of the prim (position, orientation, linear_velocity and 
                          angular_velocity) that is used after each reset.
        """
        return self._default_state

    def post_reset(self) -> None:
        """Resets the prim to its default state.
        """
        XFormPrim.post_reset(self)
        if not XFormPrim.non_root_articulation_link(self):
            RigidPrim.set_angular_velocity(self, self._default_state.angular_velocity)
            RigidPrim.set_linear_velocity(self, self._default_state.linear_velocity)
        return

    def get_current_dynamic_state(self) -> DynamicState:
        """ 
        Returns:
            DynamicState: the dynamic state of the rigid body including position, orientation, linear_velocity and angular_velocity.
        """
        position, orientation = self.get_world_pose()
        return DynamicState(
            position=position,
            orientation=orientation,
            linear_velocity=self.get_linear_velocity(),
            angular_velocity=self.get_angular_velocity(),
        )
