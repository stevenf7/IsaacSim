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


class XFormPrimState(object):
    def __init__(self, position, orientation):
        self.position = position
        self.orientation = orientation


class DynamicState(object):
    def __init__(self, position, orientation, linear_velocity, angular_velocity):
        self.position = position
        self.orientation = orientation
        self.linear_velocity = linear_velocity
        self.angular_velocity = angular_velocity


class JointsState(object):
    def __init__(self, positions, velocities, efforts):
        self.positions = positions
        self.velocities = velocities
        self.efforts = efforts


class ArticulationAction(object):
    def __init__(
        self,
        joint_positions: Optional[np.ndarray] = None,
        joint_velocities: Optional[np.ndarray] = None,
        joint_efforts: Optional[np.ndarray] = None,
    ):
        """[summary]

        Args:
            joint_positions (Optional, optional): [description]. Defaults to None.
            joint_velocities (Optional, optional): [description]. Defaults to None.
            joint_efforts (Optional, optional): [description]. Defaults to None.
        """
        self.joint_positions = joint_positions
        self.joint_velocities = joint_velocities
        self.joint_efforts = joint_efforts

    def get_dof_action(self, index: int):
        """[summary]

        Args:
            index (int): [description]

        Returns:
            [type]: [description]
        """
        if self.joint_efforts is not None and self.joint_efforts[index] is not None:
            return {"effort": self.joint_efforts[index]}
        else:
            dof_action = dict()
            if self.joint_velocities is not None and self.joint_velocities[index] is not None:
                dof_action["velocity"] = self.joint_velocities[index]
            if self.joint_positions is not None and self.joint_positions[index] is not None:
                dof_action["position"] = self.joint_positions[index]
            return dof_action
