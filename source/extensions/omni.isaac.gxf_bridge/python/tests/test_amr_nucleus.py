# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import asyncio
import os
import pathlib

import omni.kit.test
from omni.isaac.core import World
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import create_new_stage_async, update_stage_async
from omni.isaac.gxf_bridge import AmrAssetTier, check_nucleus_path, get_gxf_nucleus_path
from omni.isaac.version import get_version


class TestNucleus(omni.kit.test.AsyncTestCase):
    async def setUp(self, device="cpu"):
        World.clear_instance()
        await create_new_stage_async()
        self._my_world = World(stage_units_in_meters=1.0, device=device)
        await self._my_world.initialize_simulation_context_async()
        await omni.kit.app.get_app().next_update_async()
        self._my_world.scene.add_default_ground_plane()
        pass

    async def tearDown(self):
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await update_stage_async()
        World.clear_instance()
        pass

    async def test_check_nucleus_path(self):
        with self.assertRaises(NotADirectoryError):
            check_nucleus_path("/foo")

        asset_root_path = get_assets_root_path()
        path = "/Isaac/"
        self.assertEqual(check_nucleus_path(path), asset_root_path + path)

    async def test_get_gxf_nucleus_path(self):
        asset_root_path = get_assets_root_path()

        self.assertEqual(
            get_gxf_nucleus_path(asset_tier=AmrAssetTier.STAGING),
            os.path.join(asset_root_path, "Projects/isaac_amr_envoy/Staging/"),
        )

        self.assertEqual(
            get_gxf_nucleus_path(asset_tier=AmrAssetTier.STAGING, isaac_amr_version="2.0"),
            os.path.join(asset_root_path, "Projects/isaac_amr_envoy/Staging/"),
        )

        self.assertEqual(
            get_gxf_nucleus_path(asset_tier=AmrAssetTier.RELEASE_CANDIDATE),
            os.path.join(asset_root_path, "Projects/isaac_amr_envoy/Release/"),
        )

        self.assertEqual(
            get_gxf_nucleus_path(asset_tier=AmrAssetTier.RELEASE_CANDIDATE, isaac_amr_version="2.0"),
            os.path.join(asset_root_path, "Projects/isaac_amr_envoy/Release/"),
        )

        app_version_core, _, _, _, _, _, _, _ = get_version()
        self.assertEqual(
            get_gxf_nucleus_path(asset_tier=AmrAssetTier.EXTERNAL_RELEASE),
            os.path.join(asset_root_path, "Isaac/Samples/Isaac_AMR/2.0/"),
        )

        with self.assertRaises(NotADirectoryError):
            get_gxf_nucleus_path(asset_tier=AmrAssetTier.EXTERNAL_RELEASE, isaac_amr_version="0.0")

        with self.assertRaises(NotADirectoryError):
            get_gxf_nucleus_path(asset_tier=0)
