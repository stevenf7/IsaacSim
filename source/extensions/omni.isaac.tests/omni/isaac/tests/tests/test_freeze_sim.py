# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.core.utils.stage import open_stage_async, update_stage_async
import omni.kit.test
import carb
import asyncio

# Having a test class derived from omni.kit.test.AsyncTestCase declared on the root of module will
# make it auto-discoverable by omni.kit.test
class TestFreezeSim(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        self._physics_dt = 1 / 60  # duration of physics frame in seconds

        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)

        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(1 / self._physics_dt))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(1 / self._physics_dt))

        carb.settings.get_settings().set_bool("/app/file/ignoreUnsavedOnExit", True)
        carb.settings.get_settings().set_bool("/app/settings/persistent", False)
        carb.settings.get_settings().set_bool("/app/asyncRendering", False)
        carb.settings.get_settings().set_bool("/app/asyncRenderingLowLatency", False)
        carb.settings.get_settings().set_bool("/app/asyncRenderingLowLatency", False)

        await update_stage_async()

        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await update_stage_async()
        self._dc = None
        await update_stage_async()
        pass

    async def test_freeze_sim(self):
        usd_path = self._dc_extension_path + "/data/usd/robots/franka/franka.usd"

        for i in range(100):
            (result, error) = await open_stage_async(usd_path)
            await update_stage_async()
            self.assertTrue(result)

            print(f"Opened Stage {i+1} times without freezing")
