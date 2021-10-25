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
import math

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dr import _dr
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.nucleus import find_nucleus_server


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDomainRandomizerTransform(omni.kit.test.AsyncTestCaseFailOnLogError):
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

    # Unit test for movement component
    async def test_transform_component_instancer(self):
        root_layer = self._stage.GetRootLayer()
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        # Create cube
        cubeGeom = UsdGeom.Cube.Define(self._stage, default_prim_path + "/Cube")
        cubeGeom.CreateSizeAttr(100)
        # make sure the prim exists
        cube_path = default_prim_path + "/Cube"
        cube = self._stage.GetPrimAtPath(cube_path)

        instancer_path = "/instancer"
        point_instancer = UsdGeom.PointInstancer(self._stage.DefinePrim(instancer_path, "PointInstancer"))
        point_instancer.AddTranslateOp().Set((100, 0, 0))
        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(0.0, 0.0, 1.0), 45).GetQuat())
        point_instancer.AddOrientOp().Set(rot_quat)

        self.assertTrue(cube)
        # Get initial transform matrix
        xformable = UsdGeom.Xformable(cube)
        # Create DR component and check if it exists
        positions_attr = point_instancer.CreatePositionsAttr()
        orientations_attr = point_instancer.CreateOrientationsAttr()

        points = [(0, 0, 0), (100, 100, 0)]
        # second quat is a 45 degree rotation
        orientations = [Gf.Quath(1, 0, 0, 0), Gf.Quath(0.924, 0, 0, 0.383)]
        positions_attr.Set(points)
        orientations_attr.Set(orientations)

        lane_point = UsdGeom.Sphere(self._stage.DefinePrim(instancer_path + "/point", "Sphere"))
        lane_point.AddScaleOp().Set(Gf.Vec3d(10, 10, 10))
        lane_point.CreateDisplayColorPrimvar().Set([(1.0, 0.0, 0.0)])
        # Attribute marker to point instancer.
        point_instancer.CreatePrototypesRel().SetTargets([lane_point.GetPath()])
        proto_indices_attr = point_instancer.CreateProtoIndicesAttr()
        proto_indices_attr.Set([0] * len(points))

        result, prim = omni.kit.commands.execute(
            "CreateTransformComponentCommand",
            prim_paths=[cube_path],
            target_point_instancer_paths=[instancer_path],
            enable_sequential_behavior=True,
        )

        await omni.kit.app.get_app().next_update_async()
        self._dr.toggle_manual_mode()
        self._dr.randomize_once()
        await omni.kit.app.get_app().next_update_async()
        transform_matrix_1 = xformable.GetLocalTransformation()
        self._dr.randomize_once()
        await omni.kit.app.get_app().next_update_async()
        transform_matrix_2 = xformable.GetLocalTransformation()
        self._dr.toggle_manual_mode()
        await omni.kit.app.get_app().next_update_async()
        # first point is rotated by 45 degrees due to instancer, and then translated 100 in x
        self.assertTrue(np.allclose(np.array(transform_matrix_1.ExtractTranslation()), np.array([100, 0, 0])))
        rotation_1 = transform_matrix_1.ExtractRotation()
        self.assertTrue(np.allclose(np.array(rotation_1.GetAxis()), np.array([0, 0, 1])))
        self.assertAlmostEqual(rotation_1.GetAngle(), 45, delta=0.1)

        # second point is translated by 100 in x but also rotated by 45 due to instancer transform
        self.assertTrue(
            np.allclose(
                np.array(transform_matrix_2.ExtractTranslation()), np.array([100, math.sqrt(100 ** 2 + 100 ** 2), 0])
            )
        )
        # because we rotate by 45 degrees from instancer transform and the second point, we should be at 90
        rotation_2 = transform_matrix_2.ExtractRotation()
        self.assertTrue(np.allclose(np.array(rotation_2.GetAxis()), np.array([0, 0, 1])))
        self.assertAlmostEqual(rotation_2.GetAngle(), 90, delta=0.1)

        pass
