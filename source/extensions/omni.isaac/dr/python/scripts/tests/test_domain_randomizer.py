# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import omni.kit.undo
import omni.kit.commands
import omni.isaac.DrSchema as DrSchema
import carb.tokens
import os
import asyncio
from pxr import Gf, Kind, Sdf, Usd, UsdGeom, UsdShade, UsdLux, UsdShade

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dr import _dr
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.kit.builtin.commands.usd_commands import *

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
        pass

    # After running each test
    async def tearDown(self):
        self._editor.stop()
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
        self._editor.play()
        # Make cube Xformable
        xformable = UsdGeom.Xformable(cube)
        # Create DR component and check if it exists
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/color_component", False)
        prim = DrSchema.ColorComponent.Define(self._stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("color_component"))
        color_comp_path = default_prim_path + "/color_component"
        color_comp = self._stage.GetPrimAtPath(color_comp_path)
        self.assertTrue(color_comp)
        # Set parameter for DR component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateFirstColorAttr().Set((float(0.0), float(0.0), float(0.0)))
        prim.CreateSecondColorAttr().Set((float(1.0), float(1.0), float(1.0)))
        prim.CreateDurationAttr().Set(float(0.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        # Let the material load
        await asyncio.sleep(10.0)
        # Validate color material prim
        color_mat_path = default_prim_path + "/Colors/color_component/OmniPBR_2"
        color_mat = self._stage.GetPrimAtPath(color_mat_path)
        self.assertTrue(color_mat)
        # Validate attribute for randomizing color
        color_attr = color_mat.GetAttribute("inputs:diffuse_color_constant")
        self.assertIsNotNone(color_attr)
        color_value_1 = Gf.Vec3f(color_attr.Get())
        await omni.kit.asyncapi.next_update()
        color_value_2 = Gf.Vec3f(color_attr.Get())
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
        # Start Simulation
        self._editor.play()
        # Get initial transform matrix
        xformable = UsdGeom.Xformable(cube)
        transform_matrix_1 = xformable.GetLocalTransformation()
        # Create DR component and check if it exists
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/movement_component", False)
        prim = DrSchema.MovementComponent.Define(self._stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("movement_component"))
        mov_comp_path = default_prim_path + "/movement_component"
        mov_comp = self._stage.GetPrimAtPath(mov_comp_path)
        self.assertTrue(mov_comp)
        # Set parameter for DR component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateXRangeAttr().Set((float(0.0), float(10.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(10.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(10.0)))
        prim.CreateDurationAttr().Set(float(0.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        # Enable manual mode and execute DR once
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
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
        prim = DrSchema.RotationComponent.Define(self._stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("rotation_component"))
        rot_comp_path = default_prim_path + "/rotation_component"
        rot_comp = self._stage.GetPrimAtPath(rot_comp_path)
        self.assertTrue(rot_comp)
        # Set parameter for DR component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateXRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateDurationAttr().Set(float(0.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        # Enable manual mode and execute DR once
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
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
        prim = DrSchema.ScaleComponent.Define(self._stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("scale_component"))
        scale_comp_path = default_prim_path + "/scale_component"
        scale_comp = self._stage.GetPrimAtPath(scale_comp_path)
        self.assertTrue(scale_comp)
        # Set parameter for DR component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateXRangeAttr().Set((float(0.0), float(5.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(5.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(5.0)))
        prim.CreateDurationAttr().Set(float(0.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        # Enable manual mode and execute DR once
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        self._dr.toggle_manual_mode()
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

        self._editor.play()
        # Create DR component and check if it exists
        path = omni.kit.utils.get_stage_next_free_path(self._stage, default_prim_path + "/light_component", False)
        prim = DrSchema.LightComponent.Define(self._stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set("light_component")
        light_comp_path = default_prim_path + "/light_component"
        light_comp = self._stage.GetPrimAtPath(light_comp_path)
        self.assertTrue(light_comp)
        # Set parameter for DR component
        prim.CreatePrimPathsRel().AddTarget(light_path)
        prim.CreateFirstColorAttr().Set((float(0.0), float(0.0), float(0.0)))
        prim.CreateSecondColorAttr().Set((float(1.0), float(1.0), float(1.0)))
        prim.CreateIntensityRangeAttr().Set((float(40000.0), float(70000.0)))
        prim.CreateTemperatureRangeAttr().Set((float(1500.0), float(6500.0)))
        prim.CreateEnableTemperatureAttr().Set(bool(True))
        prim.CreateDurationAttr().Set(float(0.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
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
