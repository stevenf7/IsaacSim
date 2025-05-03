# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import asyncio

import carb
import omni.kit.test
import usdrt
from isaacsim.core.utils.prims import define_prim
from isaacsim.core.utils.stage import (
    add_reference_to_stage,
    clear_stage,
    create_new_stage_async,
    get_current_stage,
    update_stage_async,
    use_stage,
)
from isaacsim.storage.native import get_assets_root_path_async
from pxr import Usd, UsdGeom


class TestStage(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await update_stage_async()
        pass

    async def test_clear_stage(self):
        await create_new_stage_async()
        prim = define_prim(prim_path="/Test", prim_type="Xform")
        self.assertTrue(prim.IsValid())
        assets_root_path = await get_assets_root_path_async()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
        asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        robot = add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_1")
        await update_stage_async()

        self.assertTrue(robot.IsValid())
        clear_stage()
        await update_stage_async()
        self.assertFalse(prim.IsValid())
        self.assertFalse(robot.IsValid())
        pass

    async def test_add_reference_to_stage_units(self):
        from isaacsim.core.utils.stage import clear_stage

        clear_stage()

        # setup different units
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 0.01)

        assets_root_path = await get_assets_root_path_async()
        if assets_root_path is None:
            raise Exception("Asset root path doesn't exist")
        asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka")

        xform_ref = stage.GetPrimAtPath("/World/Franka")
        self.assertEqual(xform_ref.GetAttribute("xformOp:scale").Get(), [1.0, 1.0, 1.0])
        scale_attr = xform_ref.GetAttribute("xformOp:scale:unitsResolve")
        self.assertTrue(not scale_attr)

        clear_stage()

        # enable omni.usd.metrics.assembler.ui
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_manager.set_extension_enabled_immediate("omni.usd.metrics.assembler.ui", True)
        ext_manager.set_extension_enabled_immediate("omni.usd.metrics.assembler.physics", False)

        # setup different units
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 0.01)

        assets_root_path = await get_assets_root_path_async()
        if assets_root_path is None:
            raise Exception("Asset root path doesn't exist")
        asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka")

        xform_ref = stage.GetPrimAtPath("/World/Franka")
        self.assertEqual(xform_ref.GetAttribute("xformOp:scale:unitsResolve").Get(), [100.0, 100.0, 100.0])

        ext_manager.set_extension_enabled_immediate("omni.usd.metrics.assembler.physics", True)
        ext_manager.set_extension_enabled_immediate("omni.usd.metrics.assembler.ui", False)

    async def test_context_manager(self):
        await create_new_stage_async()
        stage_in_memory = Usd.Stage.CreateInMemory()
        default_stage = omni.usd.get_context().get_stage()
        self.assertIs(get_current_stage(), default_stage)
        # - USD stage
        with use_stage(stage_in_memory):
            self.assertIs(get_current_stage(), stage_in_memory)
            self.assertIsNot(get_current_stage(), default_stage)
        self.assertIs(get_current_stage(), default_stage)
        # - get Fabric stage
        with use_stage(stage_in_memory):
            self.assertIsInstance(get_current_stage(fabric=True), usdrt.Usd.Stage)
        self.assertIsInstance(get_current_stage(fabric=True), usdrt.Usd.Stage)
