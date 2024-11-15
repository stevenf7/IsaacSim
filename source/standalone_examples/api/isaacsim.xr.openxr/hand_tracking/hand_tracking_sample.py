# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os

import numpy as np
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False}, experience=f'{os.environ["EXP_PATH"]}/isaacsim.exp.xr.openxr.kit')

from isaacsim.core.api import World
from isaacsim.core.api.materials.omni_pbr import OmniPBR
from isaacsim.core.api.objects import VisualCuboid
from isaacsim.xr.openxr import OpenXR, OpenXRSpec

openxr = OpenXR()
my_world = World(stage_units_in_meters=1.0)


for joint_idx in range(int(OpenXRSpec.HandJointEXT.XR_HAND_JOINT_LITTLE_TIP_EXT) + 1):
    my_world.scene.add(
        VisualCuboid(
            prim_path=f"/left_cube_{joint_idx}",
            name=f"left_cube_{joint_idx}",
            position=np.array([0, 0, 0.5]),
            size=0.01,
            color=np.array([255, 0, 0]),
        )
    )

    my_world.scene.add(
        VisualCuboid(
            prim_path=f"/right_cube_{joint_idx}",
            name=f"right_cube_{joint_idx}",
            position=np.array([0, 0, 0.5]),
            size=0.01,
            color=np.array([255, 0, 0]),
        )
    )

my_world.reset()
reset_needed = False
while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_stopped() and not reset_needed:
        reset_needed = True
    if my_world.is_playing():
        if reset_needed:
            my_world.reset()
            reset_needed = False

        def update_joints(joints, prim_prefix):
            if joints is not None:
                for joint_idx in range(int(OpenXRSpec.HandJointEXT.XR_HAND_JOINT_LITTLE_TIP_EXT) + 1):
                    location_flags = joints[joint_idx].locationFlags
                    if (
                        location_flags & OpenXRSpec.XR_SPACE_LOCATION_POSITION_VALID_BIT
                        and location_flags & OpenXRSpec.XR_SPACE_LOCATION_ORIENTATION_VALID_BIT
                    ):
                        joint_pos = joints[joint_idx].pose.position
                        joint_quat = joints[joint_idx].pose.orientation
                        obj = my_world.scene.get_object(f"{prim_prefix}{joint_idx}")
                        obj.set_world_pose(
                            (joint_pos.x, -joint_pos.z, joint_pos.y),
                            (joint_quat.w, joint_quat.x, -joint_quat.z, joint_quat.y),
                        )
                        obj.set_visibility(True)
                    else:
                        my_world.scene.get_object(f"{prim_prefix}{joint_idx}").set_visibility(False)

        update_joints(openxr.locate_hand_joints(OpenXRSpec.XrHandEXT.XR_HAND_LEFT_EXT), "left_cube_")
        update_joints(openxr.locate_hand_joints(OpenXRSpec.XrHandEXT.XR_HAND_RIGHT_EXT), "right_cube_")

simulation_app.close()
