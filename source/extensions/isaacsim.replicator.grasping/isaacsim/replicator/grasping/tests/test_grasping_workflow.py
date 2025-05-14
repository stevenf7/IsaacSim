# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import os

import omni.kit.app
import omni.kit.commands
import omni.usd
from isaacsim.replicator.grasping.grasping_manager import GraspingManager
from pxr import UsdGeom

DEFAULT_SAMPLER_CONFIG = {
    "sampler_type": "antipodal",
    "num_candidates": 10,
    "num_orientations": 1,
    "gripper_maximum_aperture": 0.2,
    "gripper_standoff_fingertips": 0.2,
    "gripper_approach_direction": (0, 0, 1),
    "grasp_align_axis": (0, 1, 0),
    "orientation_sample_axis": (0, 1, 0),
    "lateral_sigma": 0.0,
    "random_seed": 12,
    "verbose": True,
}

OBJECT_ASSET_URL = "Isaac/Props/YCB/Axis_Aligned/003_cracker_box.usd"


class TestGraspingWorkflow((omni.kit.test.AsyncTestCase)):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        omni.usd.get_context().close_stage()
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

    async def test_grasp_pose_generation(self):
        stage = omni.usd.get_context().get_stage()
        await omni.kit.app.get_app().next_update_async()

        object_path = "/World/ObjectAsset"
        omni.kit.commands.execute("CreateMeshPrimWithDefaultXformCommand", prim_type="Cube", prim_path=object_path)
        await omni.kit.app.get_app().next_update_async()
        object_prim = omni.usd.get_context().get_stage().GetPrimAtPath(object_path)
        if not object_prim.HasAttribute("xformOp:scale"):
            UsdGeom.Xformable(object_prim).AddScaleOp()
        object_prim.GetAttribute("xformOp:scale").Set((0.1, 0.1, 0.1))

        grasping_manager = GraspingManager()
        grasping_manager.set_object_prim_path(object_path)
        self.assertEqual(grasping_manager.get_object_prim_path(), object_path)

        success_generation = grasping_manager.generate_grasp_poses(config=DEFAULT_SAMPLER_CONFIG)
        print(f"Success generation: {success_generation}")
        print(f"Grasp locations: {grasping_manager.grasp_locations}")
