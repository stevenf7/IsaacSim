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
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.stage import is_stage_loading


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDomainRandomizerMesh(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dr = _dr.acquire_dr_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._omni_pbr_data = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${kit}/../../library/mdl/Base/OmniPBR.mdl")
        )

        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport_legacy.get_viewport_interface()
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
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/mesh_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMeshComponentCommand",
            parent_prim=["/World"],
            mesh_list=[
                self._nucleus_path + "/Props/Blocks/nvidia_cube.usd",
                self._nucleus_path + "/Props/Rubiks_Cube/rubiks_cube.usd",
            ],
            mesh_range=[3, 5],
            seed=12345,
        )
        self._timeline.play()
        while is_stage_loading():
            await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(1.0)
        parent_prim = self._stage.GetPrimAtPath("/World")
        self.assertGreater(len(parent_prim.GetChildren()), 1)
        pass

    async def test_mesh_component_parent(self):
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/mesh_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMeshComponentCommand",
            path=path,
            mesh_list=[
                self._nucleus_path + "/Props/Blocks/nvidia_cube.usd",
                self._nucleus_path + "/Props/Rubiks_Cube/rubiks_cube.usd",
            ],
            mesh_range=[3, 5],
            seed=12345,
        )
        self._timeline.play()
        while is_stage_loading():
            await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(1.0)
        parent_prim = self._stage.GetPrimAtPath(path)
        self.assertGreater(len(parent_prim.GetChildren()), 1)
        pass
