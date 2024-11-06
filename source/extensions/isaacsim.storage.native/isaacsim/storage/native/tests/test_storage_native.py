# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import json

import carb
import omni.kit.commands
import omni.kit.test

# import omni.kit.usd
from isaacsim.storage.native import get_assets_root_path_async


class TestStorageNative(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_get_assets_root_path_async(self):
        default_assets_url = carb.settings.get_settings().get("/persistent/isaac/asset_root/default")
        result = await get_assets_root_path_async()
        self.assertEqual(result, default_assets_url)
