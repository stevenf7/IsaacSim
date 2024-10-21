# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

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

        left_hand_joints = openxr.locate_hand_joints(OpenXRSpec.XrHandEXT.XR_HAND_LEFT_EXT)
        if left_hand_joints is not None:
            for joint_idx in range(int(OpenXRSpec.HandJointEXT.XR_HAND_JOINT_LITTLE_TIP_EXT) + 1):
                joint_pos = left_hand_joints[joint_idx].pose.position
                my_world.scene.get_object(f"left_cube_{joint_idx}").set_world_pose(
                    (joint_pos.x, -joint_pos.z, joint_pos.y)
                )

        right_hand_joints = openxr.locate_hand_joints(OpenXRSpec.XrHandEXT.XR_HAND_RIGHT_EXT)
        if right_hand_joints is not None:
            for joint_idx in range(int(OpenXRSpec.HandJointEXT.XR_HAND_JOINT_LITTLE_TIP_EXT) + 1):
                joint_pos = right_hand_joints[joint_idx].pose.position
                my_world.scene.get_object(f"right_cube_{joint_idx}").set_world_pose(
                    (joint_pos.x, -joint_pos.z, joint_pos.y)
                )

simulation_app.close()
