# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
from typing import Optional

from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.extensions import get_extension_path_from_name
from isaacsim.robot_motion.motion_generation.articulation_kinematics_solver import ArticulationKinematicsSolver
from isaacsim.robot_motion.motion_generation.lula.kinematics import LulaKinematicsSolver


class KinematicsSolver(ArticulationKinematicsSolver):
    """Kinematics Solver for UR10 robot.  This class loads a LulaKinematicsSolver object

    Args:
        robot_articulation (SingleArticulation): An initialized Articulation object representing this UR10
        end_effector_frame_name (Optional[str]): The name of the UR10 end effector.  If None, an end effector link will
            be automatically selected.  Defaults to None.
        attach_gripper (Optional[bool]): If True, a URDF will be loaded that includes a suction gripper.  Defaults to False.
    """

    def __init__(
        self,
        robot_articulation: SingleArticulation,
        end_effector_frame_name: Optional[str] = None,
        attach_gripper: Optional[bool] = False,
    ) -> None:

        mg_extension_path = get_extension_path_from_name("isaacsim.robot_motion.motion_generation")

        if attach_gripper:
            robot_urdf_path = os.path.join(mg_extension_path, "motion_policy_configs/ur10/ur10_robot_suction.urdf")
        else:
            robot_urdf_path = os.path.join(mg_extension_path, "motion_policy_configs/ur10/ur10_robot.urdf")
        if attach_gripper:
            robot_description_yaml_path = os.path.join(
                mg_extension_path, "motion_policy_configs/ur10/rmpflow_suction/ur10_robot_description.yaml"
            )
        else:
            robot_description_yaml_path = os.path.join(
                mg_extension_path, "motion_policy_configs/ur10/rmpflow/ur10_robot_description.yaml"
            )

        self._kinematics = LulaKinematicsSolver(
            robot_description_path=robot_description_yaml_path, urdf_path=robot_urdf_path
        )

        if end_effector_frame_name is None:
            if attach_gripper:
                end_effector_frame_name = "ee_suction_link"
            else:
                end_effector_frame_name = "ee_link"

        ArticulationKinematicsSolver.__init__(self, robot_articulation, self._kinematics, end_effector_frame_name)

        return
