# Copyright (c) 2018-2023, NVIDIA CORPORATION.  All rights reserved.
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
import carb
import omni.hydratexture
import carb.tokens
from pxr import UsdGeom, UsdPhysics
import omni.kit.commands
import omni
import omni.kit
import omni.usd
from omni.isaac.core.utils.render_product import create_hydra_texture
import omni.replicator.core as rep
from omni.isaac.core import SimulationContext


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
class TestRTXRotaryLidar(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        # TODO: RTX sensors are not supported on windows yet
        if sys.platform == "win32":
            return

        self._settings = carb.settings.acquire_settings_interface()
        self._hydra_texture_factory = omni.hydratexture.acquire_hydra_texture_factory_interface()

        self._usd_context_name = ""
        self._usd_context = omni.usd.get_context(self._usd_context_name)
        await self._usd_context.new_stage_async()
        # This needs to be set so that kit updates match physics updates
        self._physics_rate = 60
        self._sensor_rate = 120
        self._settings.set_bool("/app/runLoops/main/rateLimitEnabled", True)
        self._settings.set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        self._settings.set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        pass

    async def tearDown(self):

        self._usd_context.close_stage()
        await self.linux_gpu_shutdown_workaround()

        self._hydra_texture_factory = None
        self._settings = None

    async def linux_gpu_shutdown_workaround(self):
        async def wait_frames(frames: int = 10):
            for _ in range(frames):
                await omni.kit.app.get_app().next_update_async()

        await wait_frames()
        omni.usd.release_all_hydra_engines(self._usd_context)
        await wait_frames()

    async def test_rtx_lidar_point_cloud(self):
        stage = omni.usd.get_context().get_stage()
        simulation_app = omni.kit.app.get_app()
        add_cube(stage, "/World/cube_1", (1, 20, 1), (5, 0, 0), physics=False)
        add_cube(stage, "/World/cube_2", (1, 20, 1), (-5, 0, 0), physics=False)
        add_cube(stage, "/World/cube_3", (20, 1, 1), (0, 5, 0), physics=False)
        add_cube(stage, "/World/cube_4", (20, 1, 1), (0, -5, 0), physics=False)
        await simulation_app.next_update_async()

        config = "Example_Rotary"
        _, sensor = omni.kit.commands.execute("IsaacSensorCreateRtxLidar", path="/sensor", parent=None, config=config)
        _, render_product_path = create_hydra_texture([1, 1], sensor.GetPath().pathString)
        rv = "RtxLidar"
        writer = rep.writers.get(rv + "DebugDrawPointCloud")
        writer.attach([render_product_path])
        await simulation_app.next_update_async()
        await simulation_app.next_update_async()
        simulation_context = SimulationContext(
            physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0, stage_units_in_meters=1.0
        )

        simulation_context.play()
        for i in range(10):
            await simulation_app.next_update_async()

        # cleanup and shutdown
        simulation_context.stop()

    pass
