# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.utils.kinematics import InverseKinematicsSolver as BaseInverseKinematicsSolver
from omni.isaac.core.utils.extensions import get_extension_path_from_name
import os
from typing import Optional


class InverseKinematicsSolver(BaseInverseKinematicsSolver):
    """[summary]

        Args:
            name (str): [description]
            robot_prim_path (str): [description]
            robot_urdf_path (Optional[str], optional): [description]. Defaults to None.
            robot_description_yaml_path (Optional[str], optional): [description]. Defaults to None.
            end_effector_frame_name (Optional[str], optional): [description]. Defaults to None.
        """

    def __init__(
        self,
        name: str,
        robot_prim_path: str,
        robot_urdf_path: Optional[str] = None,
        robot_description_yaml_path: Optional[str] = None,
        end_effector_frame_name: Optional[str] = None,
    ) -> None:
        mg_extension_path = get_extension_path_from_name("omni.isaac.motion_generation")
        if robot_urdf_path is None:
            robot_urdf_path = os.path.join(mg_extension_path, "policy_configs/franka/lula_franka_gen.urdf")
        if robot_description_yaml_path is None:
            robot_description_yaml_path = os.path.join(
                mg_extension_path, "policy_configs/franka/rmpflow/robot_descriptor.yaml"
            )
        if end_effector_frame_name is None:
            end_effector_frame_name = "right_gripper"
        BaseInverseKinematicsSolver.__init__(
            self,
            name=name,
            robot_urdf_path=robot_urdf_path,
            robot_description_yaml_path=robot_description_yaml_path,
            robot_prim_path=robot_prim_path,
            end_effector_frame_name=end_effector_frame_name,
        )
        return
