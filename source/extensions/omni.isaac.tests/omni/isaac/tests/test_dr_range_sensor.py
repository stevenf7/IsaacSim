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
from pxr import Gf, Sdf, UsdGeom, UsdShade, UsdLux, UsdPhysics
from omni.isaac.range_sensor import _range_sensor

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dr import _dr
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.prims.geometry_prim import GeometryPrim


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDRRangeSensor(omni.kit.test.AsyncTestCaseFailOnLogError):
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
    async def test_dr_movement_lidar(self):
        self._scene = UsdPhysics.Scene.Define(self._stage, Sdf.Path("/World/physicsScene"))
        self._scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        self._scene.CreateGravityMagnitudeAttr().Set(981.0)
        default_prim_path = str(self._stage.GetDefaultPrim().GetPath())
        # Create cube
        cubeGeom = UsdGeom.Cube.Define(self._stage, default_prim_path + "/Cube")
        cubeGeom.CreateSizeAttr(10)
        GeometryPrim(prim_path=cubeGeom.GetPath(), name="cube", collision=True)
        await omni.kit.app.get_app().next_update_async()
        result, lidar = omni.kit.commands.execute(
            "RangeSensorCreateLidar",
            path="/World/Lidar",
            parent=None,
            min_range=0,
            max_range=100.0,
            draw_points=True,
            draw_lines=True,
            horizontal_fov=360.0,
            vertical_fov=30.0,
            horizontal_resolution=1.0,
            vertical_resolution=1.0,
            rotation_rate=0.0,
            high_lod=False,
            yaw_offset=0.0,
        )
        await omni.kit.app.get_app().next_update_async()
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            prim_paths=["/World/Lidar"],
            min_range=(0.0, 0.0, 0.0),
            max_range=(100.0, 100.0, 0.0),
            target_position=None,
            target_paths=None,
            duration=0.0,
            include_children=False,
        )
        lidarInterface = _range_sensor.acquire_lidar_sensor_interface()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        for frame in range(60):
            await omni.kit.app.get_app().next_update_async()
            pointcloud = lidarInterface.get_point_cloud_data("/World/Lidar")
            self.assertGreater(len(pointcloud), 0)
        pass
