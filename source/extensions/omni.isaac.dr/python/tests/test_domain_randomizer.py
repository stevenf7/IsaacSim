# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.commands
import carb.tokens
import os
import asyncio
import numpy as np
from pxr import Gf, Usd, UsdGeom, UsdShade, UsdLux

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dr import _dr
from omni.isaac.dynamic_control import _dynamic_control
from omni.kit.builtin.commands.usd_commands import *
from .common import load_test_file, set_scene_physics_type


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
        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()
        self._editor = omni.kit.editor.get_editor_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        pass

    def is_loading(self):
        time, message, loaded, loading = self._editor.get_current_renderer_status()
        return loading > 0

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
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/color_component", False)
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
        while self.is_loading():
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

    # Unit test for movement component
    async def test_movement_component(self):
        root_layer = self._stage.GetRootLayer()
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
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/movement_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            path=path,
            prim_paths=[cube_path],
            min_range=(0.0, 0.0, 0.0),
            max_range=(10.0, 10.0, 10.0),
            target_position=None,
            target_paths=None,
            duration=0.0,
            include_children=False,
        )
        mov_comp_path = default_prim_path + "/movement_component"
        mov_comp = self._stage.GetPrimAtPath(mov_comp_path)
        self.assertTrue(mov_comp)
        # Enable manual mode and execute DR once
        await omni.kit.app.get_app().next_update_async()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.app.get_app().next_update_async()
        # Get new transform matrix
        transform_matrix_2 = xformable.GetLocalTransformation()
        # Check if rotation components are same and translation components are different
        self.assertTrue(
            Gf.IsClose(transform_matrix_1.ExtractRotationMatrix(), transform_matrix_2.ExtractRotationMatrix(), 0.00001)
        )
        self.assertFalse(
            Gf.IsClose(transform_matrix_1.ExtractTranslation(), transform_matrix_2.ExtractTranslation(), 0.00001)
        )
        pass

    # Unit test for movement component for articulated robots
    async def test_movement_component_franka(self):
        (result, error) = await load_test_file(self._extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu=False)
        # Start Simulation and wait
        self._timeline.play()
        await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        # Get initial transform matrix
        self._dc.wake_up_articulation(art)
        root_body = self._dc.get_articulation_root_body(art)

        pos = self._dc.get_rigid_body_pose(root_body).p
        rot = self._dc.get_rigid_body_pose(root_body).r
        self.assertTupleEqual(
            tuple(np.round(np.array([pos.x, pos.y, pos.z]), 3)), tuple(np.round(np.array([0, 0, 0]), 3))
        )
        self.assertTupleEqual(
            tuple(np.round(np.array([rot.x, rot.y, rot.z, rot.w]), 3)), tuple(np.round(np.array([0, 0, 0, 1]), 3))
        )
        # Create DR component and check if it exists
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            path="/movement_component",
            prim_paths=["/panda"],
            min_range=(50.0, 50.0, 10.0),
            max_range=(100.0, 100.0, 10.0),
            target_position=None,
            target_paths=None,
            duration=0.0,
            include_children=False,
        )
        # Enable manual mode and execute DR once
        await omni.kit.app.get_app().next_update_async()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.app.get_app().next_update_async()
        # Check if rotation components are same and translation components are different
        new_pose_p = (88.2894, 79.2465, 10)
        pos = self._dc.get_rigid_body_pose(root_body).p
        rot = self._dc.get_rigid_body_pose(root_body).r
        self.assertTupleEqual(
            tuple(np.round(np.array([pos.x, pos.y, pos.z]), 3)), tuple(np.round(np.array(new_pose_p), 3))
        )
        self.assertTupleEqual(
            tuple(np.round(np.array([rot.x, rot.y, rot.z, rot.w]), 3)), tuple(np.round(np.array([0, 0, 0, 1]), 3))
        )
        pass

    # Unit test for movement component for articulated robots
    async def test_movement_component_carter(self):
        (result, error) = await load_test_file(self._extension_path + "/data/usd/robots/carter/carter.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu=False)
        # Start Simulation and wait
        self._timeline.play()
        await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/carter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        # Get initial transform matrix
        self._dc.wake_up_articulation(art)
        root_body = self._dc.get_articulation_root_body(art)

        pos = self._dc.get_rigid_body_pose(root_body).p
        rot = self._dc.get_rigid_body_pose(root_body).r
        # Create DR component and check if it exists
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            path="/movement_component",
            prim_paths=["/carter"],
            min_range=(50.0, 50.0, 10.0),
            max_range=(100.0, 100.0, 10.0),
            target_position=None,
            target_paths=None,
            duration=0.0,
            include_children=False,
        )
        # Enable manual mode and execute DR once
        await omni.kit.app.get_app().next_update_async()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.app.get_app().next_update_async()
        # Check if rotation components are same and translation components are different
        new_pose_p = (88.2894, 79.2465, 10)
        pos = self._dc.get_rigid_body_pose(root_body).p
        rot = self._dc.get_rigid_body_pose(root_body).r
        self.assertTupleEqual(
            tuple(np.round(np.array([pos.x, pos.y, pos.z]), 3)), tuple(np.round(np.array(new_pose_p), 3))
        )
        self.assertTupleEqual(
            tuple(np.round(np.array([rot.x, rot.y, rot.z, rot.w]), 3)),
            tuple(np.round(np.array([0.0, 0.002, -0.0, 1.0]), 3)),
        )
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
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/rotation_component", False)
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
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/scale_component", False)
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
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/light_component", False)
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
