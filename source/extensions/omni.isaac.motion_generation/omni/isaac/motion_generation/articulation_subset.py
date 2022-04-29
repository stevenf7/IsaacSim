# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.core.articulations.articulation import Articulation
import numpy as np
from typing import List


class ArticulationSubset:
    """
    A utility class for viewing a subset of the joints in a robot Articulation object.  This class can be helpful in two ways:

    1) The order of joints returned by a robot Articulation may not match the order of joints expected by a function 

    2) A function may only care about a subset of the joint states that are returned by a robot Articulation. 

    Example:

        Suppose the robot Articulation returns positions [0,1,2] for joints ["A","B","C"], and suppose that we pass view_joint_names = ["B","A"].

        ArticulationSubset.get_joint_positions() -> [1,0]

        ArticulationSubset.map_to_articulation_order([1,0]) -> [0,1,None]

    Args:
        robot_articulation (Articulation): An initialized Articulation object representing the simulated robot
        view_joint_names (List[str]): A list of joint names whose order determines the order of the joints returned by functions like get_joint_positions() 
    """

    def __init__(self, robot_articulation: Articulation, view_joint_names: List[str]) -> None:
        self._robot_articulation = robot_articulation
        self._view_joint_inds = [self._robot_articulation.get_dof_index(joint) for joint in view_joint_names]

    def get_joint_positions(self) -> np.array:
        """Get joint positions for the joint names that were passed into this articulation view on initialization.
        The indices of the joint positions returned correspond to the indices of the joint names.

        Returns:
            np.array: joint positions 
        """
        return self._robot_articulation.get_joint_positions()[self._view_joint_inds]

    def get_joint_velocities(self) -> np.array:
        """Get joint velocities for the joint names that were passed into this articulation view on initialization.
        The indices of the joint velocities returned correspond to the indices of the joint names.

        Returns:
            np.array: joint velocities 
        """
        return self._robot_articulation.get_joint_velocities()[self._view_joint_inds]

    def get_joint_efforts(self) -> np.array:
        """Get joint efforts for the joint names that were passed into this articulation view on initialization.
        The indices of the joint efforts returned correspond to the indices of the joint names.

        Returns:
            np.array: joint efforts 
        """
        return self._robot_articulation.get_joint_efforts()[self._view_joint_inds]

    def map_to_articulation_order(self, joint_values: np.array) -> np.array:
        """Map a set of joint values to a format consumable by the robot Articulation.  

        Args:
            joint_values (np.array): a set of joint values corresponding to the view_joint_names used to initialize this class

        Returns:
            np.array: a set of joint values that is padded with None to match the shape and order expected by the robot Articulation
        """
        action = [None] * self._robot_articulation.num_dof
        for i, j in enumerate(self._view_joint_inds):
            action[j] = joint_values[i]

        return action
