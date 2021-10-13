# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.commands
import carb
import carb.tokens
import os
import asyncio
import numpy as np
from pxr import Gf, Usd, UsdGeom, UsdShade, UsdLux

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dr import _dr
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDomainRandomizerMesh(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dr = _dr.acquire_dr_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._omni_pbr_data = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${kit}/../../library/mdl/Base/OmniPBR.mdl")
        )
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dr")
        self._extension_path = ext_manager.get_extension_path(ext_id)
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)

        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_viewport_interface()
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", False)

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        pass

    # Unit test for movement component for articulated robots
    async def test_mesh_component(self):
        pass
