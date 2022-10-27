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

import carb.tokens
import carb
import numpy as np
import omni.graph.core as og
import time
import math

from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.dynamic_control import utils as dc_utils
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.rotations import quat_to_euler_angles
from omni.isaac.core.utils.extensions import get_extension_path_from_name
from .robot_helpers import init_robot_sim, setup_robot_og, set_physics_frequency
from omni.isaac.core.utils.prims import delete_prim


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestJetBot(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)
        self.dc = _dynamic_control.acquire_dynamic_control_interface()

        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self._extension_path = get_extension_path_from_name("omni.isaac.tests")

        ## setup jetbot:
        # open local jetbot
        # (result, error) = await omni.usd.get_context().open_stage_async(self._extension_path + "/data/tests/jetbot.usd")

        # add in jetbot (from nucleus)
        self.usd_path = self._assets_root_path + "/Isaac/Robots/Jetbot/jetbot.usd"
        (result, error) = await open_stage_async(self.usd_path)

        # Make sure the stage loaded
        self.assertTrue(result)
        await omni.kit.app.get_app().next_update_async()
        set_physics_frequency()

        # setup omnigraph
        self.graph_path = "/ActionGraph"
        graph, self.odom_node = setup_robot_og(
            self.graph_path, "left_wheel_joint", "right_wheel_joint", "/jetbot", 0.0325, 0.118
        )

        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_jetbot_loading(self):

        delete_prim("/ActionGraph")
        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        # get the dofbot
        self.ar = self.dc.get_articulation("/jetbot")
        self.chassis = self.dc.get_articulation_root_body(self.ar)
        self.starting_pos = np.array(self.dc.get_rigid_body_pose(self.chassis).p)

        self.wheel_left = self.dc.find_articulation_dof(self.ar, "left_wheel_joint")
        self.wheel_right = self.dc.find_articulation_dof(self.ar, "right_wheel_joint")

        # move the jetbot
        self.dc.set_dof_velocity_target(self.wheel_left, 0.5)
        self.dc.set_dof_velocity_target(self.wheel_right, 0.5)

        await dc_utils.simulate(2, self.dc, self.ar)

        self.current_pos = np.array(self.dc.get_rigid_body_pose(self.chassis).p)

        delta = np.linalg.norm(self.current_pos - self.starting_pos)
        print("Diff is ", delta)
        self.assertTrue(delta > 0.02)

        pass

    async def test_jetbot_forward(self):

        odom_position = og.Controller.attribute("outputs:position", self.odom_node)
        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/jetbot")
        l_wheel = self.dc.get_rigid_body("/jetbot/left_wheel")

        # go straight
        forward_velocity = 0.6
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
        await omni.kit.app.get_app().next_update_async()

        # wait until const velocity reached
        for i in range(100):
            await omni.kit.app.get_app().next_update_async()

        init_pos = None
        for i in range(400):
            # set init_pos
            if init_pos is None:
                init_pos = float(og.DataView.get(odom_position)[0])
                init_y = float(og.DataView.get(odom_position)[1])
                init_time = time.time()

            await omni.kit.app.get_app().next_update_async()
            curr_vel = float(og.DataView.get(odom_velocity)[0])
            self.assertAlmostEqual(curr_vel, forward_velocity, delta=forward_velocity / 5)
            self.assertAlmostEqual(
                curr_vel, (self.dc.get_rigid_body_angular_velocity(l_wheel)[1]) * 0.0325, delta=forward_velocity / 5
            )

        end_time = time.time()
        final_pos = og.DataView.get(odom_position)

        loop_del = (400.0 / 60.0) * forward_velocity
        dist_del = (end_time - init_time) * forward_velocity

        if abs(loop_del - (final_pos[0] - init_pos)) < abs(dist_del - (final_pos[0] - init_pos)):
            self.assertAlmostEqual(final_pos[0] - init_pos, loop_del, delta=0.5)
            self.assertAlmostEqual(final_pos[1] - init_y, 0.0, delta=0.15)
        else:
            self.assertAlmostEqual(final_pos[0] - init_pos, dist_del, delta=0.5)
            self.assertAlmostEqual(final_pos[1] - init_y, 0.0, delta=0.15)

        self._timeline.stop()

        pass

    async def test_jetbot_spin(self):

        odom_orientation = og.Controller.attribute("outputs:orientation", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/jetbot")
        l_wheel = self.dc.get_rigid_body("/jetbot/left_wheel")

        # spin
        angular_velocity = 0.4
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
            angular_velocity
        )
        await omni.kit.app.get_app().next_update_async()

        # wait until const velocity reached
        for i in range(100):
            await omni.kit.app.get_app().next_update_async()

        init_pos = None
        for i in range(400):
            # set init_pos
            if init_pos is None:
                init_time = time.time()
                init_pos = quat_to_euler_angles(og.DataView.get(odom_orientation))[0]
                print(og.DataView.get(odom_orientation))
                print(init_pos)
            await omni.kit.app.get_app().next_update_async()
            curr_ang_vel = float(og.DataView.get(odom_ang_vel)[2])
            self.assertAlmostEqual(curr_ang_vel, angular_velocity, delta=5e-2)

            magn = math.sqrt(
                (self.dc.get_rigid_body_angular_velocity(l_wheel)[0] * 0.0325 * 2 / 0.118) ** 2
                + (self.dc.get_rigid_body_angular_velocity(l_wheel)[1] * 0.0325 * 2 / 0.118) ** 2
            )
            self.assertAlmostEqual(curr_ang_vel, magn, delta=5e-2)

        end_time = time.time()

        final_pos = quat_to_euler_angles(og.DataView.get(odom_orientation))[0]
        if final_pos < 0:
            final_pos = 2 * math.pi + final_pos
        print("final-init orientation: " + str(final_pos - init_pos))

        loop_del = (400.0 / 60.0) * angular_velocity
        dist_del = (end_time - init_time) * angular_velocity

        if abs(loop_del - (final_pos - init_pos)) < abs(dist_del - (final_pos - init_pos)):
            self.assertAlmostEqual(final_pos - init_pos, loop_del, delta=0.5)
        else:
            self.assertAlmostEqual(final_pos - init_pos, dist_del, delta=0.5)

        self._timeline.stop()
        pass

    # general, slowly building up speed testcase
    async def test_jetbot_accel_generic(self):

        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/jetbot")

        # go straight
        forward_velocity = 0.05
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)

        # wait until const velocity reached
        for i in range(100):
            await omni.kit.app.get_app().next_update_async()

        for x in range(2, 5):
            forward_velocity = x * 0.15
            og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(
                forward_velocity
            )
            print(x)
            print(forward_velocity)
            for i in range(50):
                await omni.kit.app.get_app().next_update_async()
            for i in range(100):
                if og.DataView.get(odom_ang_vel)[2] > 0.8:
                    print("spinning out of control!")
                    print("linear velocity: " + str(forward_velocity))
                    self._timeline.stop()
                else:
                    self.assertAlmostEqual(og.DataView.get(odom_velocity)[0], forward_velocity, delta=5e-2)
                await omni.kit.app.get_app().next_update_async()

        self._timeline.stop()

        pass

    # braking from different init speeds
    async def test_jetbot_brake(self):

        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/jetbot")

        # go straight
        forward_velocity = 0.5
        angular_velocity = 0.9
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
            angular_velocity
        )

        # wait until const velocity reached
        for i in range(150):
            await omni.kit.app.get_app().next_update_async()

        curr_t = 0
        for i in range(800):
            if i - curr_t >= 200:
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(0.0)
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(0.0)
                for j in range(100):
                    await omni.kit.app.get_app().next_update_async()

                self.assertAlmostEqual(og.DataView.get(odom_velocity)[0], 0.0, delta=5e-1)
                self.assertAlmostEqual(og.DataView.get(odom_ang_vel)[2], 0.0, delta=5e-1)

                self._timeline.stop()
                await omni.kit.app.get_app().next_update_async()

                forward_velocity += 0.1
                angular_velocity += 0.1

                curr_t = i
                self._timeline.play()
                await omni.kit.app.get_app().next_update_async()

                await init_robot_sim(self.dc, "/jetbot")

                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(
                    forward_velocity
                )
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
                    angular_velocity
                )

                for j in range(100):
                    await omni.kit.app.get_app().next_update_async()

            await omni.kit.app.get_app().next_update_async()

        self._timeline.stop()

        pass

    async def test_jetbot_spin_speedup(self):
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        for x in range(1, 6):
            # spin

            # Start Simulation and wait
            self._timeline.play()
            await omni.kit.app.get_app().next_update_async()

            await init_robot_sim(self.dc, "/jetbot")
            l_wheel = self.dc.get_rigid_body("/jetbot/left_wheel")

            angular_velocity = 0.6 * x
            og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
                angular_velocity
            )

            await omni.kit.app.get_app().next_update_async()

            # wait until const velocity reached
            for i in range(100):
                await omni.kit.app.get_app().next_update_async()

            for i in range(200):
                await omni.kit.app.get_app().next_update_async()
                curr_ang_vel = float(og.DataView.get(odom_ang_vel)[2])

                self.assertAlmostEqual(curr_ang_vel, angular_velocity, delta=5e-2)
                magn = math.sqrt(
                    (self.dc.get_rigid_body_angular_velocity(l_wheel)[0] * 0.0325 * 2 / 0.118) ** 2
                    + (self.dc.get_rigid_body_angular_velocity(l_wheel)[1] * 0.0325 * 2 / 0.118) ** 2
                )
                self.assertAlmostEqual(curr_ang_vel, magn, delta=5e-2)

        self._timeline.stop()

        pass

    # accel no drop
    async def test_jetbot_accel_no_drop(self):

        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/jetbot")

        # go straight
        forward_velocity = 0.2
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
        await omni.kit.app.get_app().next_update_async()

        # wait until const velocity reached
        for i in range(100):
            await omni.kit.app.get_app().next_update_async()

        curr_t = 0
        for i in range(800):
            if i - curr_t >= 200:
                self._timeline.stop()
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(0)
                await omni.kit.app.get_app().next_update_async()
                forward_velocity += 0.2
                print("linear velocity: " + str(forward_velocity))
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(
                    forward_velocity
                )

                curr_t = i
                self._timeline.play()

                # wait until const velocity reached
                for j in range(100):
                    await omni.kit.app.get_app().next_update_async()

            if og.DataView.get(odom_ang_vel)[2] > 0.8:
                print("spinning out of control!")
                print("linear velocity: " + str(forward_velocity))
                self._timeline.stop()

            else:
                self.assertAlmostEqual(og.DataView.get(odom_velocity)[0], forward_velocity, delta=0.2)

            await omni.kit.app.get_app().next_update_async()

        self._timeline.stop()

        pass

    # go in circle
    async def test_jetbot_circle(self):

        odom_position = og.Controller.attribute("outputs:position", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # comment out to stay under exttest timeout

        await omni.kit.app.get_app().next_update_async()

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/jetbot")

        # go straight
        forward_velocity = 0.3
        angular_velocity = 0.5
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
            angular_velocity
        )

        # wait until const velocity reached
        for i in range(300):
            await omni.kit.app.get_app().next_update_async()

        time_t = None
        init = False

        for i in range(2000):
            if (
                abs(float(og.DataView.get(odom_position)[0])) < 0.005
                and abs(float(og.DataView.get(odom_position)[1])) < 0.005
            ):
                if time_t is None:
                    time_t = time.time()
                    print("init_time:" + str(time_t))
                else:
                    if time.time() - time_t > 5 and not init:
                        time_t = time.time() - time_t
                        init = True
                        print("time_del:" + str(time_t))

            if og.DataView.get(odom_ang_vel)[2] > 0.3:
                self.assertAlmostEqual(og.DataView.get(odom_ang_vel)[2], angular_velocity, delta=0.2)

            await omni.kit.app.get_app().next_update_async()

        print("time delta: " + str(time_t))
        print((time_t) * angular_velocity)
        self.assertAlmostEqual(2 * math.pi, (time_t) * angular_velocity, delta=1)

        self._timeline.stop()
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(0)
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(0)

        await omni.kit.app.get_app().next_update_async()

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/jetbot")

        forward_velocity = -0.3
        angular_velocity = 0.5
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
            angular_velocity
        )

        # wait until const velocity reached
        for i in range(300):
            await omni.kit.app.get_app().next_update_async()

        time_t = None
        init = False

        for i in range(2100):
            if (
                abs(float(og.DataView.get(odom_position)[0])) < 0.005
                and abs(float(og.DataView.get(odom_position)[1])) < 0.01
            ):
                if time_t is None:
                    time_t = time.time()
                    print("init_time:" + str(time_t))
                else:
                    if time.time() - time_t > 5 and not init:
                        time_t = time.time() - time_t
                        init = True
                        print("time_del:" + str(time_t))

            if og.DataView.get(odom_ang_vel)[2] > 0.3:
                self.assertAlmostEqual(og.DataView.get(odom_ang_vel)[2], angular_velocity, delta=0.2)

            await omni.kit.app.get_app().next_update_async()

        print("time delta: " + str(time_t))
        print((time_t) * angular_velocity)
        self.assertAlmostEqual(2 * math.pi, (time_t) * angular_velocity, delta=1)

        self._timeline.stop()

        pass

    # corner case: quick accel from zero
    # async def test_jetbot_accel_drop_reset(self):
    #     odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
    #     odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

    #     # Start Simulation and wait
    #     self._timeline.play()
    #     await omni.kit.app.get_app().next_update_async()

    #     await init_robot_sim(self.dc, "/jetbot")
    #     l_wheel = self.dc.get_rigid_body("/jetbot/left_wheel")

    #     forward_velocity = 0.2
    #     og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)

    #     # wait until const velocity reached
    #     for i in range(50):
    #         await omni.kit.app.get_app().next_update_async()

    #     curr_t = 0
    #     for i in range(1600):
    #         if i - curr_t >= 200:
    #             self._timeline.stop()
    #             og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(0)
    #             await omni.kit.app.get_app().next_update_async()
    #             curr_t = i
    #             self._timeline.play()
    #             await omni.kit.app.get_app().next_update_async()

    #             await init_robot_sim(self.dc, "/jetbot")
    #             # l_wheel = self.dc.get_rigid_body("/jetbot/left_wheel")

    #             # wait until const velocity reached
    #             for j in range(100):
    #                 await omni.kit.app.get_app().next_update_async()

    #             forward_velocity += 0.2
    #             og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(
    #                 forward_velocity
    #             )

    #             print("forward velocity: " + str(forward_velocity))

    #             # wait until const velocity reached
    #             for j in range(100):
    #                 await omni.kit.app.get_app().next_update_async()

    #         if og.DataView.get(odom_ang_vel)[2] > 0.8:
    #             print("spinning out of control!")
    #             print("linear velocity: " + str(forward_velocity))
    #             self._timeline.stop()

    #         else:
    #             curr_vel = float(og.DataView.get(odom_velocity)[0])
    #             self.assertAlmostEqual(curr_vel, forward_velocity, delta=5e-1)
    #             self.assertAlmostEqual(
    #                 curr_vel, (self.dc.get_rigid_body_angular_velocity(l_wheel)[1]) * 0.0325, delta=0.25
    #             )
    #             print(self.dc.get_rigid_body_angular_velocity(l_wheel)[1] * 0.0325)
    #             print("correct forward velocity: " + str(forward_velocity))
    #         await omni.kit.app.get_app().next_update_async()

    #     self._timeline.stop()

    #     pass
