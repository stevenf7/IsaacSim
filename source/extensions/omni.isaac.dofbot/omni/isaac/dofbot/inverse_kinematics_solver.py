# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.utils.kinematics import InverseKinematicsSolver as BaseInverseKinematicsSolver
from omni.isaac.core.utils.extensions import get_extension_id, get_extension_path
import os


class InverseKinematicsSolver(BaseInverseKinematicsSolver):
    def __init__(
        self,
        name,
        robot_prim_path,
        robot_urdf_path=None,
        robot_description_yaml_path=None,
        end_effector_frame_name=None,
    ):
        extension_id = get_extension_id("omni.isaac.motion_generation")
        mg_extension_path = get_extension_path(ext_id=extension_id)
        if robot_urdf_path is None:
            robot_urdf_path = os.path.join(mg_extension_path, "policy_configs/dofbot/arm.urdf")
        if robot_description_yaml_path is None:
            robot_description_yaml_path = os.path.join(
                mg_extension_path, "policy_configs/dofbot/rmpflow/robot_descriptor.yaml"
            )
        if end_effector_frame_name is None:
            end_effector_frame_name = "link5"
        BaseInverseKinematicsSolver.__init__(
            self,
            name=name,
            robot_urdf_path=robot_urdf_path,
            robot_description_yaml_path=robot_description_yaml_path,
            robot_prim_path=robot_prim_path,
            end_effector_frame_name=end_effector_frame_name,
        )
        return
