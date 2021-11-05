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
from omni.isaac.dynamic_control.scripts.utils import set_scene_physics_type
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.physics import simulate_async
from omni.isaac.core.utils.extensions import get_extension_path_from_name

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDomainRandomizerMovement(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dr = _dr.acquire_dr_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._omni_pbr_data = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${kit}/../../library/mdl/Base/OmniPBR.mdl")
        )
        self._dc_extension_path = get_extension_path_from_name("omni.isaac.dynamic_control")

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
        path = omni.usd.get_stage_next_free_path(self._stage, default_prim_path + "/movement_component", False)
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
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu=False)
        # Start Simulation and wait
        self._timeline.play()
        await simulate_async(1.0)
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        # Get initial transform matrix
        self._dc.wake_up_articulation(art)
        root_body = self._dc.get_articulation_root_body(art)

        initial_pos = self._dc.get_rigid_body_pose(root_body).p
        initial_rot = self._dc.get_rigid_body_pose(root_body).r
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
            tuple(np.round(np.array([rot.x, rot.y, rot.z, rot.w]), 3)),
            tuple(np.round(np.array([initial_rot.x, initial_rot.y, initial_rot.z, initial_rot.w]), 3)),
        )
        pass

    # Unit test for movement component for articulated robots
    async def test_movement_component_carter(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/carter/carter.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu=False)
        # Start Simulation and wait
        self._timeline.play()
        await simulate_async(1.0)
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/carter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        # Get initial transform matrix
        self._dc.wake_up_articulation(art)
        root_body = self._dc.get_articulation_root_body(art)

        initial_pos = self._dc.get_rigid_body_pose(root_body).p
        initial_rot = self._dc.get_rigid_body_pose(root_body).r
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
            tuple(np.round(np.array([initial_rot.x, initial_rot.y, initial_rot.z, initial_rot.w]), 3)),
        )
        pass
