# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio

import carb
import omni.kit.test
from omni.isaac.core.utils.prims import define_prim, is_prim_path_valid
from omni.isaac.gxf_bridge import AmrAssetTier, GxfRobotType, define_gxf_robot_prim


class TestGxfRobot(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        # This needs to be set so that kit updates match physics updates
        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        self.conveyor_node = None
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        self.conveyor_node = None
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_define_gxf_robot_prim(self):
        prim_path_fail = "/fail"
        define_prim(prim_path_fail)

        with self.assertRaises(Exception):
            define_gxf_robot_prim(prim_path_fail)

        prim_path_robot = "/robot"
        define_gxf_robot_prim(prim_path_robot, gxf_robot_type=GxfRobotType.CARTER_V2_3, asset_tier=AmrAssetTier.STAGING)
        self.assertTrue(is_prim_path_valid(prim_path_robot))
