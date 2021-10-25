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
from omni.isaac.core.utils.stage import is_stage_loading
from omni.isaac.core.utils.nucleus import find_nucleus_server

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDomainRandomizer(omni.kit.test.AsyncTestCaseFailOnLogError):
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

    # Unit test for rotation component
    async def test_rotation_component(self):
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        # Create cube
        cubeGeom = UsdGeom.Cube.Define(self._stage, default_prim_path + "/Cube")
        # make sure the prim exists
        cube_path = default_prim_path + "/Cube"
        cube = self._stage.GetPrimAtPath(cube_path)
        self.assertTrue(cube)
        # Get initial transform matrix
        xformable = UsdGeom.Xformable(cube)
        transform_matrix_1 = xformable.GetLocalTransformation()
        # Create DR component and check if it exists
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/rotation_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateRotationComponentCommand",
            path=path,
            prim_paths=[cube_path],
            min_range=(0.0, 0.0, 0.0),
            max_range=(360.0, 360.0, 360.0),
            duration=0.0,
            include_children=False,
        )
        rot_comp_path = default_prim_path + "/rotation_component"
        rot_comp = self._stage.GetPrimAtPath(rot_comp_path)
        self.assertTrue(rot_comp)
        # Enable manual mode and execute DR once
        await omni.kit.app.get_app().next_update_async()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.app.get_app().next_update_async()
        # Get new transform matrix
        transform_matrix_2 = xformable.GetLocalTransformation()
        # Check if rotation components are different and translation components are same
        self.assertFalse(
            Gf.IsClose(transform_matrix_1.ExtractRotationMatrix(), transform_matrix_2.ExtractRotationMatrix(), 0.00001)
        )
        self.assertTrue(
            Gf.IsClose(transform_matrix_1.ExtractTranslation(), transform_matrix_2.ExtractTranslation(), 0.00001)
        )
        pass

    # Unit test for scale component
    async def test_scale_component(self):
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        # Create cube
        cubeGeom = UsdGeom.Cube.Define(self._stage, default_prim_path + "/Cube")
        # make sure the prim exists
        cube_path = default_prim_path + "/Cube"
        cube = self._stage.GetPrimAtPath(cube_path)
        self.assertTrue(cube)
        # Get initial transform matrix
        xformable = UsdGeom.Xformable(cube)
        transform_matrix_1 = xformable.GetLocalTransformation()
        # Create DR component and check if it exists
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/scale_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateScaleComponentCommand",
            path=path,
            prim_paths=[cube_path],
            min_range=(0.5, 0.5, 0.5),
            max_range=(5.0, 5.0, 5.0),
            uniform_scaling=False,
            duration=0.0,
            include_children=False,
        )
        scale_comp_path = default_prim_path + "/scale_component"
        scale_comp = self._stage.GetPrimAtPath(scale_comp_path)
        self.assertTrue(scale_comp)
        # Enable manual mode and execute DR once
        await omni.kit.app.get_app().next_update_async()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.app.get_app().next_update_async()
        # Get new transform matrix
        transform_matrix_2 = xformable.GetLocalTransformation()
        # Check if transformation matrices are different
        self.assertFalse(Gf.IsClose(transform_matrix_1, transform_matrix_2, 0.00001))
        pass

    # Unit test for light component
    async def test_light_component(self):
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        # Create rect light
        lightGeom = UsdLux.RectLight.Define(self._stage, default_prim_path + "/RectLight")
        # make sure the prim exists
        light_path = default_prim_path + "/RectLight"
        light = self._stage.GetPrimAtPath(light_path)
        self.assertTrue(light)
        # Start Simulation

        self._timeline.play()
        # Create DR component and check if it exists
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/light_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateLightComponentCommand",
            path=path,
            light_paths=[light_path],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            intensity_range=(40000.0, 70000.0),
            temperature_range=(1500.0, 6500.0),
            enable_temperature=True,
            duration=0.0,
            include_children=False,
        )
        light_comp_path = default_prim_path + "/light_component"
        light_comp = self._stage.GetPrimAtPath(light_comp_path)
        self.assertTrue(light_comp)
        # Validate attribute for randomizing light
        light_color_attr = light.GetAttribute("color")
        self.assertIsNotNone(light_color_attr)
        light_color_temp_attr = light.GetAttribute("colorTemperature")
        self.assertIsNotNone(light_color_temp_attr)
        light_color_intensity_attr = light.GetAttribute("intensity")
        self.assertIsNotNone(light_color_intensity_attr)
        light_color_value_1 = light_color_attr.Get()
        light_color_temp_value_1 = light_color_temp_attr.Get()
        light_color_intensity_value_1 = light_color_intensity_attr.Get()
        await omni.kit.app.get_app().next_update_async()
        light_color_value_2 = light_color_attr.Get()
        light_color_temp_value_2 = light_color_temp_attr.Get()
        light_color_intensity_value_2 = light_color_intensity_attr.Get()
        # Check if light property values are different after one frame
        self.assertFalse(Gf.IsClose(light_color_value_1, light_color_value_2, 0.00001))
        self.assertFalse(Gf.IsClose(light_color_temp_value_1, light_color_temp_value_2, 0.00001))
        self.assertFalse(Gf.IsClose(light_color_intensity_value_1, light_color_intensity_value_2, 0.00001))
        pass

    # Unit test for texture component performance
    async def test_texture_component_fps(self):
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
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/texture_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateTextureComponentCommand",
            path=path,
            prim_paths=[cube_path],
            enable_project_uvw=True,
            texture_list=[
                self._nucleus_path + "/Samples/DR/Materials/Textures/checkered.png",
                self._nucleus_path + "/Samples/DR/Materials/Textures/marble_tile.png",
                self._nucleus_path + "/Samples/DR/Materials/Textures/picture_a.png",
                self._nucleus_path + "/Samples/DR/Materials/Textures/picture_b.png",
                self._nucleus_path + "/Samples/DR/Materials/Textures/textured_wall.png",
                self._nucleus_path + "/Samples/DR/Materials/Textures/checkered_color.png",
            ],
            ignored_class_list=[],
            grouped_class_list=[],
            duration=0.0,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(1.0)
        texture_comp_path = default_prim_path + "/texture_component"
        texture_comp = self._stage.GetPrimAtPath(texture_comp_path)
        self.assertTrue(texture_comp)
        # Let the material load
        await omni.kit.app.get_app().next_update_async()
        while is_stage_loading():
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

    # Unit test for DR layer name API
    async def test_dr_layer_name(self):
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        is_anon_in_layer = "anon" in self._dr.get_dr_layer_name()
        self.assertTrue(is_anon_in_layer)
        pass
