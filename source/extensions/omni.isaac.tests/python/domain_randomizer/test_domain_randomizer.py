# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import omni.kit.commands
import carb.tokens
import os
import asyncio
from pxr import Gf, Usd, UsdGeom, UsdShade, UsdLux

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dr import _dr
from omni.kit.builtin.commands.usd_commands import *


def get_data_file(file_name: str):
    if os.path.isabs(file_name):
        path_to_file = file_name
    else:
        path_to_file = os.path.abspath(
            os.path.join(carb.tokens.get_tokens_interface().resolve("${app}"), "..", "data", "usd", file_name)
        )
    return path_to_file


async def load_test_file(test_file_name: str):
    if not Usd.Stage.IsSupportedFile(test_file_name):
        raise ValueError("Only USD files can be loaded with this method")

    path_to_file = get_data_file(test_file_name)

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    (result, error) = await omni.kit.asyncapi.open_stage(path_to_file)
    usd_context.enable_save_to_recent_files()
    return (result, error)


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDomainRandomizer(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dr = _dr.acquire_dr_interface()
        self._omni_pbr_data = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${kit}/../../library/mdl/Base/OmniPBR.mdl")
        )
        await omni.kit.asyncapi.connect("ov-isaac-dev:3009", "testing", "testing")
        await omni.kit.asyncapi.new_stage()
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
        await omni.kit.asyncapi.next_update()
        while self.is_loading():
            await omni.kit.asyncapi.next_update()
        await omni.kit.asyncapi.next_update()
        # Validate color material prim
        color_mat_path = default_prim_path + "/Colors/color_component/OmniPBR_2/Shader"
        color_mat = self._stage.GetPrimAtPath(color_mat_path)
        self.assertTrue(color_mat)
        # Validate attribute for randomizing color
        color_attr = color_mat.GetAttribute("inputs:diffuse_color_constant")
        self.assertIsNotNone(color_attr)
        color_value_1 = color_attr.Get()
        await omni.kit.asyncapi.next_update()
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
        await omni.kit.asyncapi.next_update()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.asyncapi.next_update()
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
        await omni.kit.asyncapi.next_update()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.asyncapi.next_update()
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
        await omni.kit.asyncapi.next_update()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
        await omni.kit.asyncapi.next_update()
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
        await omni.kit.asyncapi.next_update()
        light_color_value_2 = light_color_attr.Get()
        light_color_temp_value_2 = light_color_temp_attr.Get()
        light_color_intensity_value_2 = light_color_intensity_attr.Get()
        # Check if light property values are different after one frame
        self.assertFalse(Gf.IsClose(light_color_value_1, light_color_value_2, 0.00001))
        self.assertFalse(Gf.IsClose(light_color_temp_value_1, light_color_temp_value_2, 0.00001))
        self.assertFalse(Gf.IsClose(light_color_intensity_value_1, light_color_intensity_value_2, 0.00001))
        pass
