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

import omni.kit.usd
import carb.tokens
import gc
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.core.utils.nucleus import get_assets_root_path
from .common import PyaliceApp, create_application, add_cube, create_physics_scene
from pxr import Gf
from omni.isaac.core.utils.physics import simulate_async

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceUSS(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        context = omni.usd.get_context()
        self._stage = context.get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._asset_path = self._reb_extension_path

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.assertTrue(create_application()[1])
        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        gc.collect()
        pass

    def create_scene(self):
        create_physics_scene(self._stage)
        add_cube(self._stage, "/cube_1", 100, (100, 0, 0))
        add_cube(self._stage, "/cube_2", 100, (100, 200, 0))
        add_cube(self._stage, "/cube_3", 100, (-150, -150, 0))

    def add_ultrasonic(self, ultrasonicPath):

        emitter_poses = [
            (Gf.Quatd(0.951057, 0, 0, -0.309017), Gf.Vec3d(25, 0.0, 25)),
            (Gf.Quatd(0.987688, 0, 0, -0.156434), Gf.Vec3d(25, 50.0, 25)),
            (Gf.Quatd(0.987688, 0, 0, 0.156434), Gf.Vec3d(25, 100, 25)),
            (Gf.Quatd(0.951057, 0, 0, 0.309017), Gf.Vec3d(25, 150, 25)),
            (Gf.Quatd(-0.309017, 0, 0, 0.951056), Gf.Vec3d(-25, 0.0, 25)),
            (Gf.Quatd(-0.156435, 0, 0, 0.987688), Gf.Vec3d(-25, 50.0, 25)),
            (Gf.Quatd(0.156434, 0, 0, 0.987688), Gf.Vec3d(-25, 100, 25)),
            (Gf.Quatd(0.309017, 0, 0, 0.951057), Gf.Vec3d(-25, 150, 25)),
            (Gf.Quatd(0.760406, 0, 0, -0.649448), Gf.Vec3d(12.5, 0.0, 25)),
            (Gf.Quatd(0.649448, 0, 0, -0.760406), Gf.Vec3d(12.5, 0.0, 25)),
            (Gf.Quatd(0.760406, 0, 0, 0.649448), Gf.Vec3d(12.5, 150, 25)),
            (Gf.Quatd(0.649448, 0, 0, 0.760406), Gf.Vec3d(12.5, 150, 25)),
        ]

        emitters = []
        for pose in emitter_poses:
            result, emitter_prim = omni.kit.commands.execute(
                "RangeSensorCreateUltrasonicEmitter",
                path="/World/UltrasonicEmitter",
                per_ray_intensity=0.4,
                yaw_offset=0.0,
                adjacency_list=[],
            )
            emitter_prim.GetPrim().GetAttribute("xformOp:translate").Set(pose[1])
            emitter_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(
                Gf.Rotation(pose[0]).Decompose((1, 0, 0), (0, 1, 0), (0, 0, 1))
            )
            emitters.append(emitter_prim)
        emitter_paths = [emitter.GetPath() for emitter in emitters]

        # Add ultrasonic
        result, ultrasonic = omni.kit.commands.execute(
            "RangeSensorCreateUltrasonicArray",
            path=ultrasonicPath,
            min_range=0.4,
            max_range=2.0,
            draw_lines=True,
            horizontal_fov=20.0,
            vertical_fov=10.0,
            horizontal_resolution=0.4,
            vertical_resolution=0.8,
            num_bins=224,
            emitter_prims=emitter_paths,
            firing_group_prims=[],
        )

        return ultrasonic

    async def test_component(self):
        self.add_ultrasonic("/uss_array")
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateUltrasonic",
            path="/REB_Ultrasonic",
            parent=None,
            output_component="output",
            output_channel="uss_envelopes",
            ultrasonic_prim_rel=["/uss_array"],
        )
        self.create_scene()
        self._timeline.play()
        await simulate_async(1.0)

    async def test_uss(self):

        self.add_ultrasonic("/uss_array")
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateUltrasonic",
            path="/REB_Ultrasonic",
            parent=None,
            output_component="output",
            output_channel="uss_envelopes",
            ultrasonic_prim_rel=["/uss_array"],
        )
        self.create_scene()
        test_app = PyaliceApp()

        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()

        self._timeline.play()
        await simulate_async(2.0)
        msg = test_app.app.receive("simulation.interface", "output", "uss_envelopes")
        buffer = msg.tensor
        self.assertTupleEqual(buffer.shape, (12, 224))
        self._timeline.stop()
        test_app.stop()
        test_app = None
