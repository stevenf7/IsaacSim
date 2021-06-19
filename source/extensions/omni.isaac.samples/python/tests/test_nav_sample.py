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
from omni.isaac.dynamic_control import _dynamic_control as dc
import gc
import asyncio
import carb
from pxr import Gf
from .common import simulate
import math

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.physx.scripts.physicsUtils import add_ground_plane
from omni.isaac.samples.scripts.utils.simple_robot_controller import RobotController
from omni.isaac.samples.scripts.utils import math_utils
from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server


class TestNavSample(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._dc = dc.acquire_dynamic_control_interface()
        await omni.usd.get_context().new_stage_async()

        self._physics_rate = 60
        self._time_step = 1.0 / self._physics_rate
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        await omni.kit.app.get_app().next_update_async()

        self.assertFalse(self._dc.is_simulating())
        # Start Simulation and wait
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._usd_context = omni.usd.get_context()

        self._setup_done = False
        self._rc = None
        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        self._dc = None
        self._rc = None
        self._editor_event_subscription = None
        gc.collect()
        pass

    async def load_nav_scene(self):
        self._stage = self._usd_context.get_stage()
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        robot_usd = nucleus_server + "/Isaac/Robots/Carter/carter_sphere_wheels_lidar.usd"
        self._robot_prim_path = "/robot"
        self._robot_chassis = self._robot_prim_path + "/chassis_link"
        self._robot_wheels = ["left_wheel", "right_wheel"]
        self._robot_wheels_speed = [2, 2]

        set_up_z_axis(self._stage)
        add_ground_plane(self._stage, "/physics/groundPlane", "Z", 1000.0, Gf.Vec3f(0.0, 0, -25), Gf.Vec3f(1.0))
        setup_physics(self._stage)

        # setup high-level robot prim
        self.prim = self._stage.DefinePrim(self._robot_prim_path, "Xform")
        self.prim.GetReferences().AddReference(robot_usd)

    async def setup_controller(self):
        self._stage = self._usd_context.get_stage()
        # setup robot controller
        self._rc = RobotController(
            self._stage,
            self._timeline,
            self._dc,
            self._robot_prim_path,
            self._robot_chassis,
            self._robot_wheels,
            self._robot_wheels_speed,
            [3, 0.05],
        )
        self._rc.control_setup()
        self.imu = self._dc.get_rigid_body(self._robot_chassis)
        # start stepping
        self._editor_event_subscription = (
            omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._rc.update)
        )

    # Send forward command and check if it moved forward
    async def test_move(self):
        await self.load_nav_scene()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await self.setup_controller()
        await omni.kit.app.get_app().next_update_async()
        self._rc.control_command(1, 1)

        await simulate(2)
        imu_pose = self._dc.get_rigid_body_pose(self.imu)
        self.assertGreater(imu_pose.p.x, 0.0)
        pass

    # Send rotate in-place command and check if it rotated
    async def test_rotate(self):
        await self.load_nav_scene()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await self.setup_controller()
        await omni.kit.app.get_app().next_update_async()
        self._rc.control_command(1, -1)

        await simulate(2)
        imu_pose = self._dc.get_rigid_body_pose(self.imu)
        roll, pitch, yaw = math_utils.quaternionToEulerAngles(
            Gf.Quaternion(imu_pose.r.w, Gf.Vec3d(imu_pose.r.x, imu_pose.r.y, imu_pose.r.z))
        )
        self.assertNotEqual(yaw, 0.0)
        pass

    # Send navigate command and check if it reached the goal
    async def test_navigate(self):
        await self.load_nav_scene()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await self.setup_controller()
        await omni.kit.app.get_app().next_update_async()
        self._rc.set_goal(100, 100, 90)
        self._rc.enable_navigation(True)

        for frame in range(int(60 * 60)):
            await omni.kit.app.get_app().next_update_async()
            if self._rc.reached_goal():
                break
        imu_pose = self._dc.get_rigid_body_pose(self.imu)
        roll, pitch, yaw = math_utils.quaternionToEulerAngles(
            Gf.Quaternion(imu_pose.r.w, Gf.Vec3d(imu_pose.r.x, imu_pose.r.y, imu_pose.r.z))
        )
        self.assertAlmostEqual(imu_pose.p.x, self._rc.get_goal()[0], delta=2.0)
        self.assertAlmostEqual(imu_pose.p.y, self._rc.get_goal()[1], delta=2.0)
        self.assertAlmostEqual(yaw, math.radians(self._rc.get_goal()[2]), delta=0.1)
        pass

    # Send forward command, check if it moved forward, stop and play and then repeat
    async def test_move_stop_move(self):
        await self.load_nav_scene()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await self.setup_controller()
        await omni.kit.app.get_app().next_update_async()
        # Move forward
        self._rc.control_command(1, 1)
        await simulate(1)
        imu_pose = self._dc.get_rigid_body_pose(self.imu)
        self.assertGreater(imu_pose.p.x, 0.0)
        # Stop and play
        self._rc.control_command(0, 0)
        await simulate(1)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        # Move forward again
        self._rc.control_command(1, 1)
        await simulate(1)
        imu_pose_new = self._dc.get_rigid_body_pose(self.imu)
        self.assertAlmostEqual(imu_pose_new.p.x, imu_pose.p.x, delta=1.0)
        pass
