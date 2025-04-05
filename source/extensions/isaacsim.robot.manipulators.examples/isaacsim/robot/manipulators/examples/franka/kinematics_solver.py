# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from typing import Optional

import isaacsim.robot_motion.motion_generation.interface_config_loader as interface_config_loader
from isaacsim.core.prims import SingleArticulation
from isaacsim.robot_motion.motion_generation.articulation_kinematics_solver import ArticulationKinematicsSolver
from isaacsim.robot_motion.motion_generation.lula.kinematics import LulaKinematicsSolver


class KinematicsSolver(ArticulationKinematicsSolver):
    """Kinematics Solver for Franka robot.  This class loads a LulaKinematicsSovler object

    Args:
        robot_articulation (SingleArticulation): An initialized Articulation object representing this Franka
        end_effector_frame_name (Optional[str]): The name of the Franka end effector.  If None, an end effector link will
            be automatically selected.  Defaults to None.
    """

    def __init__(self, robot_articulation: SingleArticulation, end_effector_frame_name: Optional[str] = None) -> None:
        kinematics_config = interface_config_loader.load_supported_lula_kinematics_solver_config("Franka")
        self._kinematics = LulaKinematicsSolver(**kinematics_config)

        if end_effector_frame_name is None:
            end_effector_frame_name = "right_gripper"

        ArticulationKinematicsSolver.__init__(self, robot_articulation, self._kinematics, end_effector_frame_name)

        return
