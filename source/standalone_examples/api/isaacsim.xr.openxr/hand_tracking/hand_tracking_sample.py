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

simulation_app = SimulationApp(
    {"headless": False}, experience=f'{os.environ["EXP_PATH"]}/isaacsim.exp.base.xr.openxr.kit'
)

from isaacsim.core.api import World
from isaacsim.core.api.materials.omni_pbr import OmniPBR
from isaacsim.core.api.objects import VisualCuboid
from isaacsim.core.utils.prims import create_prim, set_prim_visibility
from isaacsim.xr.openxr import OpenXR, OpenXRSpec
from omni.isaac.core.prims import XFormPrim
from pxr import Gf, Sdf, Usd, UsdGeom

openxr = OpenXR()
my_world = World(stage_units_in_meters=1.0)

hidden_prim = create_prim("/Hidden/Prototypes", "Scope")
base_cube_path = "/Hidden/Prototypes/BaseCube"
VisualCuboid(
    prim_path=base_cube_path,
    size=0.01,
    color=np.array([255, 0, 0]),
)
set_prim_visibility(hidden_prim, False)

instancer_path = "/World/CubeInstancer"
point_instancer = UsdGeom.PointInstancer.Define(my_world.stage, instancer_path)
point_instancer.CreatePrototypesRel().SetTargets([Sdf.Path(base_cube_path)])

hand_joint_count = int(OpenXRSpec.HandJointEXT.XR_HAND_JOINT_LITTLE_TIP_EXT) + 1
joint_count = hand_joint_count * 2

# Initially hide all cubes until hands are tracked
point_instancer.CreateProtoIndicesAttr().Set([1 for _ in range(joint_count)])

positions = [Gf.Vec3f(0.0, 0.0, 0.0) for i in range(joint_count)]
point_instancer.CreatePositionsAttr().Set(positions)

orientations = [Gf.Quath(1.0, 0.0, 0.0, 0.0) for _ in range(joint_count)]
point_instancer.CreateOrientationsAttr().Set(orientations)

instancer_prim = XFormPrim(prim_path=instancer_path)
my_world.scene.add(instancer_prim)

my_world.reset()
reset_needed = False

positions_attr = point_instancer.GetPositionsAttr()
orientations_attr = point_instancer.GetOrientationsAttr()
proto_idx_attr = point_instancer.GetProtoIndicesAttr()

while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_stopped() and not reset_needed:
        reset_needed = True
    if my_world.is_playing():
        if reset_needed:
            my_world.reset()
            reset_needed = False

        current_positions = positions_attr.Get()
        current_orientations = orientations_attr.Get()
        proto_indices = proto_idx_attr.Get()

        left_joints = openxr.locate_hand_joints(OpenXRSpec.XrHandEXT.XR_HAND_LEFT_EXT) or [None] * hand_joint_count
        right_joints = openxr.locate_hand_joints(OpenXRSpec.XrHandEXT.XR_HAND_RIGHT_EXT) or [None] * hand_joint_count
        joints = left_joints + right_joints

        for joint_idx in range(joint_count):
            if joints[joint_idx] is not None:
                location_flags = joints[joint_idx].locationFlags

                if (
                    location_flags & OpenXRSpec.XR_SPACE_LOCATION_POSITION_VALID_BIT
                    and location_flags & OpenXRSpec.XR_SPACE_LOCATION_ORIENTATION_VALID_BIT
                ):
                    joint_pos = joints[joint_idx].pose.position
                    joint_quat = joints[joint_idx].pose.orientation
                    current_positions[joint_idx] = Gf.Vec3f(joint_pos.x, joint_pos.y, joint_pos.z)
                    current_orientations[joint_idx] = Gf.Quath(joint_quat.w, joint_quat.x, joint_quat.y, joint_quat.z)
                    proto_indices[joint_idx] = 0
                else:
                    proto_indices[joint_idx] = 1
            else:
                proto_indices[joint_idx] = 1

        positions_attr.Set(current_positions)
        orientations_attr.Set(current_orientations)
        proto_idx_attr.Set(proto_indices)

simulation_app.close()
