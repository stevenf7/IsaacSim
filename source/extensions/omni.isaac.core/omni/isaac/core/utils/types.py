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


class DOFInfo(object):
    def __init__(self, prim_path, handle, prim, index):
        self.prim_path = prim_path
        self.handle = handle
        self.prim = prim
        self.index = index


class PrimState(object):
    def __init__(self, position, orientation):
        self.position = position
        self.orientation = orientation


class GeometryPrimState(PrimState):
    def __init__(self, position, orientation, color):
        super().__init__(position, orientation)
        self.color = color


class CollisionPrimState(PrimState):
    def __init__(self, position, orientation, density, static_friction, dynamic_friction, restitution):
        super().__init__(position, orientation)
        self.density = density
        self.static_friction = static_friction
        self.dynamic_friction = dynamic_friction
        self.restitution = restitution


class DynamicState(object):
    def __init__(self, position, orientation, linear_velocity, angular_velocity):
        self.position = position
        self.orientation = orientation
        self.linear_velocity = linear_velocity
        self.angular_velocity = angular_velocity


class RigidPrimState(PrimState):
    def __init__(self, position, orientation, linear_velocity, angular_velocity, mass):
        super().__init__(position, orientation)
        self.linear_velocity = linear_velocity
        self.angular_velocity = angular_velocity
        self.mass = mass


class DynamicCubeState(RigidPrimState):
    def __init__(self, position, orientation, linear_velocity, angular_velocity, mass, size):
        super().__init__(position, orientation, linear_velocity, angular_velocity, mass)
        self.size = size


class VisualCubeState(GeometryPrimState):
    def __init__(self, position, orientation, color, size):
        super().__init__(position, orientation, color)
        self.size = size


class JointsState(object):
    def __init__(self, positions, velocities, torques):
        self.positions = positions
        self.velocities = velocities
        self.torques = torques


class ArticulationAction(object):
    def __init__(
        self,
        joint_positions: Optional[np.ndarray] = None,
        joint_velocities: Optional[np.ndarray] = None,
        joint_torques: Optional[np.ndarray] = None,
    ):
        """[summary]

        Args:
            joint_positions (Optional, optional): [description]. Defaults to None.
            joint_velocities (Optional, optional): [description]. Defaults to None.
            joint_torques (Optional, optional): [description]. Defaults to None.
        """
        self.joint_positions = joint_positions
        self.joint_velocities = joint_velocities
        self.joint_torques = joint_torques

    def get_dof_action(self, index: int):
        """[summary]

        Args:
            index (int): [description]

        Returns:
            [type]: [description]
        """
        if self.joint_torques is not None and self.joint_torques[index] is not None:
            return {"torque": self.joint_torques[index]}
        else:
            dof_action = dict()
            if self.joint_velocities is not None and self.joint_velocities[index] is not None:
                dof_action["velocity"] = self.joint_velocities[index]
            if self.joint_positions is not None and self.joint_positions[index] is not None:
                dof_action["position"] = self.joint_positions[index]
            return dof_action
