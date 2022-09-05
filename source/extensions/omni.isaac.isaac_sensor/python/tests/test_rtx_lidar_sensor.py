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
import sys
import carb.tokens
import numpy as np
from pxr import Gf, UsdGeom, Usd, UsdPhysics, Sdf
import omni.kit.commands
import omni
import omni.kit
import omni.usd

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.isaac_sensor import _isaac_sensor
from omni.syntheticdata import sensors
import omni.kit.viewport.utility
from omni.isaac.core.utils.viewports import add_aov_to_viewport


def add_cube(stage, path, scale, offset, physics=False):
    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)
    cubeGeom.CreateSizeAttr(1.0)
    cubeGeom.AddTranslateOp().Set(offset)
    cubeGeom.AddScaleOp().Set(scale)
    if physics:
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
        rigid_api.CreateRigidBodyEnabledAttr(True)

    UsdPhysics.CollisionAPI.Apply(cubePrim)
    return cubePrim


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRTXLidar(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        # This needs to be set so that kit updates match physics updates
        self._physics_rate = 60
        self._sensor_rate = 120
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        self._is = _isaac_sensor.acquire_imu_sensor_interface()
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.isaac_sensor")
        self._extension_path = ext_manager.get_extension_path(ext_id)

        pass

    async def test_rtx_lidar_point_cloud(self):
        # TODO: RTX sensors are not supported on windows yet
        if sys.platform == "win32":
            return
        stage = omni.usd.get_context().get_stage()
        viewport_api = omni.kit.viewport.utility.get_active_viewport()
        # in order for the sensor to generate data properly we let the viewport know that it should create a buffer for the associated render variable.
        add_aov_to_viewport(viewport_api, "RtxSensorCpu")

        cube_prim = add_cube(stage, "/World/cube_1", (1, 20, 1), (5, 0, 0), physics=False)
        cube_prim = add_cube(stage, "/World/cube_2", (1, 20, 1), (-5, 0, 0), physics=False)
        cube_prim = add_cube(stage, "/World/cube_3", (20, 1, 1), (0, 5, 0), physics=False)
        cube_prim = add_cube(stage, "/World/cube_4", (20, 1, 1), (0, -5, 0), physics=False)

        await omni.syntheticdata.sensors.next_sensor_data_async(viewport_api.id)
        rv = "RtxSensorCpu"
        sensors.get_synthetic_data().activate_node_template(
            rv + "IsaacReadRTXLidarPointCloud", 0, [viewport_api.get_render_product_path()]
        )

        await omni.syntheticdata.sensors.next_sensor_data_async(viewport_api.id)

        _, (_, sensor) = omni.kit.commands.execute("IsaacSensorCreateRtxLidar", path="/sensor", parent=None)

        await omni.kit.app.get_app().next_update_async()
        viewport_api.set_active_camera(sensor.GetPath().pathString)
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

    pass
