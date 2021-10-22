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
from pxr import Gf, UsdGeom

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dr import _dr
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.nucleus import find_nucleus_server
from .common import is_loading

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDomainRandomizerColorComponent(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dr = _dr.acquire_dr_interface()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dr")
        self._extension_path = ext_manager.get_extension_path(ext_id)

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

    # Unit test for color component
    async def test_color_component(self):
        root_layer = self._stage.GetRootLayer()
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        # Create cube
        cubeGeom = UsdGeom.Cube.Define(self._stage, default_prim_path + "/Cube")
        # make sure the prim exists
        cube_path = default_prim_path + "/Cube"
        cube = self._stage.GetPrimAtPath(cube_path)
        self.assertTrue(cube)
        # Start Simulation
        self._timeline.play()
        # Make cube Xformable
        xformable = UsdGeom.Xformable(cube)
        # Create DR component and check if it exists
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/color_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            path=path,
            prim_paths=[cube_path],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 1.0),
            duration=0.0,
            include_children=False,
        )
        color_comp_path = default_prim_path + "/color_component"
        color_comp = self._stage.GetPrimAtPath(color_comp_path)
        self.assertTrue(color_comp)
        # Let the material load
        await omni.kit.app.get_app().next_update_async()
        while is_loading():
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        # Validate color material prim
        color_mat_path = default_prim_path + "/DR/color_component/OmniPBR_2/Shader"
        color_mat = self._stage.GetPrimAtPath(color_mat_path)
        self.assertTrue(color_mat)
        # Validate attribute for randomizing color
        color_attr = color_mat.GetAttribute("inputs:diffuse_color_constant")
        self.assertIsNotNone(color_attr)
        color_value_1 = color_attr.Get()
        await omni.kit.app.get_app().next_update_async()
        color_value_2 = color_attr.Get()
        # Check if color values are different after one frame
        self.assertFalse(Gf.IsClose(color_value_1, color_value_2, 0.00001))
        pass

    # Unit test for color component performance
    async def test_color_component_fps(self):
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        # Create cube
        cubeGeom = UsdGeom.Cube.Define(self._stage, default_prim_path + "/Cube")
        # make sure the prim exists
        cube_path = default_prim_path + "/Cube"
        cube = self._stage.GetPrimAtPath(cube_path)
        self.assertTrue(cube)
        # Start Simulation
        self._timeline.play()
        # Create DR component and check if it exists
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/color_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            path=path,
            prim_paths=[cube_path],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 1.0),
            duration=0.0,
            include_children=False,
        )
        await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(1.0)
        color_comp_path = default_prim_path + "/color_component"
        color_comp = self._stage.GetPrimAtPath(color_comp_path)
        self.assertTrue(color_comp)
        # Let the material load
        await omni.kit.app.get_app().next_update_async()
        while is_loading():
            await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        # Calculate average fps
        tot_fps = 0
        num_frames = 1000
        for frame in range(num_frames):
            await omni.kit.app.get_app().next_update_async()
            tot_fps += self._viewport.get_viewport_window().get_fps()
        self._timeline.pause()
        print("Avg FPS: ", tot_fps / num_frames)
        pass
