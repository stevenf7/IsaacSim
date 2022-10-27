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
import omni.graph.core as og
import time

from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.extensions import get_extension_path_from_name
from .robot_helpers import init_robot_sim, setup_robot_og, set_physics_frequency

from omni.isaac.core.utils.stage import open_stage_async


async def ramp_velocity(forward_velocity, angular_velocity, ramp_frames, graph_path):
    for i in range(ramp_frames):
        og.Controller.attribute(graph_path + "/DifferentialController.inputs:linearVelocity").set(
            forward_velocity * ((i + 1) / ramp_frames)
        )
        og.Controller.attribute(graph_path + "/DifferentialController.inputs:angularVelocity").set(
            angular_velocity * ((i + 1) / ramp_frames)
        )
        await omni.kit.app.get_app().next_update_async()


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestCarterv1(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)
        self.dc = _dynamic_control.acquire_dynamic_control_interface()

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self._extension_path = get_extension_path_from_name("omni.isaac.tests")

        ## setup carter_v1:
        # open local carter_v1:
        # (result, error) = await omni.usd.get_context().open_stage_async(
        #     self._extension_path + "/data/tests/carter_v1.usd"
        # )

        # add in carter (from nucleus)
        self.usd_path = self._assets_root_path + "/Isaac/Robots/Carter/carter_v1.usd"
        (result, error) = await open_stage_async(self.usd_path)

        # Make sure the stage loaded
        self.assertTrue(result)
        await omni.kit.app.get_app().next_update_async()
        set_physics_frequency()

        # setup omnigraph
        self.graph_path = "/ActionGraph"
        graph, self.odom_node = setup_robot_og(self.graph_path, "left_wheel", "right_wheel", "/carter", 0.24, 0.56)

        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()
        pass

    async def test_carter_v1_forward(self):

        odom_position = og.Controller.attribute("outputs:position", self.odom_node)
        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/carter")
        l_wheel = self.dc.get_rigid_body("/carter/left_wheel_link")

        # go forward
        forward_velocity = 2.5
        angular_velocity = 0.0
        ramp_frames = 100
        await ramp_velocity(forward_velocity, angular_velocity, ramp_frames, self.graph_path)

        init_pos = None
        for i in range(400):
            # set init_pos
            if init_pos is None:
                init_time = time.time()
                init_y = float(og.DataView.get(odom_position)[1])
                init_pos = float(og.DataView.get(odom_position)[0])

            await omni.kit.app.get_app().next_update_async()

            curr_vel = float(og.DataView.get(odom_velocity)[0])
            self.assertAlmostEqual(curr_vel, forward_velocity, delta=2e-1)
            self.assertAlmostEqual(curr_vel, (self.dc.get_rigid_body_angular_velocity(l_wheel)[1]) * 0.24, delta=5e-1)

        end_time = time.time()
        final_pos = og.DataView.get(odom_position)

        print("final-init pos: " + str(final_pos - init_pos))
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

    # general, slowly building up speed testcase
    async def test_carter_v1_accel_generic(self):

        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/carter")

        # go straight
        forward_velocity = 0.5
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
        await omni.kit.app.get_app().next_update_async()

        # wait until const velocity reached
        for i in range(100):
            await omni.kit.app.get_app().next_update_async()

        for x in range(2, 5):
            forward_velocity = x * 0.25
            og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(
                forward_velocity
            )
            print(x, forward_velocity)
            for i in range(50):
                await omni.kit.app.get_app().next_update_async()
            for i in range(100):
                if og.DataView.get(odom_ang_vel)[2] > 0.8:
                    print("spinning out of control!: linear velocity: " + str(forward_velocity))
                else:
                    self.assertAlmostEqual(og.DataView.get(odom_velocity)[0], forward_velocity, delta=5e-2)
                await omni.kit.app.get_app().next_update_async()

        self._timeline.stop()

        pass

    # braking from different init speeds
    async def test_carter_v1_brake(self):

        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/carter")

        forward_velocity = 0.6
        angular_velocity = 0.6
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
            angular_velocity
        )

        # wait until const velocity reached
        for i in range(100):
            await omni.kit.app.get_app().next_update_async()

        curr_t = 0
        for i in range(800):
            if i - curr_t >= 200:
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(0.0)
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(0.0)
                for j in range(100):
                    await omni.kit.app.get_app().next_update_async()

                self.assertAlmostEqual(og.DataView.get(odom_velocity)[0], 0.0, delta=1e-1)
                self.assertAlmostEqual(og.DataView.get(odom_ang_vel)[2], 0.0, delta=1e-1)

                self._timeline.stop()
                await omni.kit.app.get_app().next_update_async()

                forward_velocity += 0.25
                angular_velocity += 0.25

                curr_t = i
                self._timeline.play()
                await omni.kit.app.get_app().next_update_async()

                await init_robot_sim(self.dc, "/carter")

                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(
                    forward_velocity
                )
                og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
                    angular_velocity
                )

                # wait until const vel
                for j in range(50):
                    await omni.kit.app.get_app().next_update_async()

            await omni.kit.app.get_app().next_update_async()

        self._timeline.stop()

        pass

    async def test_carter_v1_spin(self):

        odom_orientation = og.Controller.attribute("outputs:orientation", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/carter")
        chassis = self.dc.get_rigid_body("/carter/chassis_link")
        # l_wheel = self.dc.get_rigid_body("/carter/left_wheel_link")

        # spin
        angular_velocity = 0.5
        og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:angularVelocity").set(
            angular_velocity
        )
        await omni.kit.app.get_app().next_update_async()

        # wait until const velocity reached
        for i in range(200):
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        curr_ang_vel = float(og.DataView.get(odom_ang_vel)[2])
        dc_ang_vel = self.dc.get_rigid_body_angular_velocity(chassis)
        self.assertAlmostEqual(curr_ang_vel, angular_velocity, delta=5e-2)
        self.assertAlmostEqual(dc_ang_vel[2], angular_velocity, delta=5e-2)

        self._timeline.stop()
        pass

    # different speeds ang_vel + reset
    async def test_carter_v1_spin_speedup(self):
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        for x in range(1, 5):
            # spin
            forward_velocity = 0
            angular_velocity = 0.8 * x
            ramp_frames = 100

            # Start Simulation and wait
            self._timeline.play()
            await omni.kit.app.get_app().next_update_async()

            await init_robot_sim(self.dc, "/carter")
            chassis = self.dc.get_rigid_body("/carter/chassis_link")
            l_wheel = self.dc.get_rigid_body("/carter/left_wheel_link")
            await omni.kit.app.get_app().next_update_async()

            await ramp_velocity(forward_velocity, angular_velocity, ramp_frames, self.graph_path)

            for i in range(200):
                await omni.kit.app.get_app().next_update_async()

            curr_ang_vel = float(og.DataView.get(odom_ang_vel)[2])
            dc_ang_vel = self.dc.get_rigid_body_angular_velocity(chassis)
            self.assertAlmostEqual(curr_ang_vel, angular_velocity, delta=5e-2)
            self.assertAlmostEqual(dc_ang_vel[2], angular_velocity, delta=5e-2)

        self._timeline.stop()

        pass

    # accel no drop
    async def test_carter_v1_accel_no_drop(self):

        odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/carter")

        # go straight
        forward_velocity = 0.5
        angular_velocity = 0.0
        ramp_frames = 100
        await ramp_velocity(forward_velocity, angular_velocity, ramp_frames, self.graph_path)

        curr_t = 0
        for i in range(800):
            if i - curr_t >= 200:
                self._timeline.stop()
                await omni.kit.app.get_app().next_update_async()
                forward_velocity += 0.5
                print("linear velocity: " + str(forward_velocity))

                curr_t = i
                self._timeline.play()

                await ramp_velocity(forward_velocity, angular_velocity, ramp_frames, self.graph_path)

            if og.DataView.get(odom_ang_vel)[2] > 0.8:
                print("spinning out of control!")
                print("linear velocity: " + str(forward_velocity))
                self._timeline.stop()
            else:
                self.assertAlmostEqual(og.DataView.get(odom_velocity)[0], forward_velocity, delta=5e-2)

            await omni.kit.app.get_app().next_update_async()

        self._timeline.stop()

        pass

    # go in a circle and check if we reached the origin
    async def test_carter_v1_circle(self):

        odom_position = og.Controller.attribute("outputs:position", self.odom_node)
        odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        await init_robot_sim(self.dc, "/carter")

        forward_velocity = 1.0
        angular_velocity = 0.5
        ramp_frames = 100
        await ramp_velocity(forward_velocity, angular_velocity, ramp_frames, self.graph_path)

        for i in range(597):
            await omni.kit.app.get_app().next_update_async()

        # we should reach near origin after a fixed number of frames
        self.assertAlmostEqual(float(og.DataView.get(odom_position)[0]), 0, delta=0.01)
        self.assertAlmostEqual(float(og.DataView.get(odom_position)[1]), 0, delta=0.01)

        pass

    # # corner case: quick accel from zero
    # async def test_carter_v1_accel_drop_reset(self):
    #     odom_velocity = og.Controller.attribute("outputs:linearVelocity", self.odom_node)
    #     odom_ang_vel = og.Controller.attribute("outputs:angularVelocity", self.odom_node)

    #     # Start Simulation and wait
    #     self._timeline.play()
    #     await omni.kit.app.get_app().next_update_async()

    #     await init_robot_sim(self.dc, "/carter")
    #     l_wheel = self.dc.get_rigid_body("/carter/left_wheel_link")

    #     # weird behavior around ~ 2.0
    #     forward_velocity = 0.5
    #     og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(forward_velocity)
    #     await omni.kit.app.get_app().next_update_async()

    #     # wait until const velocity reached
    #     for i in range(100):
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

    #             await init_robot_sim(self.dc, "/carter")

    #             forward_velocity += 0.5
    #             og.Controller.attribute(self.graph_path + "/DifferentialController.inputs:linearVelocity").set(
    #                 forward_velocity
    #             )

    #             # wait until const velocity reached
    #             for j in range(100):
    #                 await omni.kit.app.get_app().next_update_async()

    #         if og.DataView.get(odom_ang_vel)[2] > 0.8:
    #             print("spinning out of control!")
    #             print("linear velocity: " + str(forward_velocity))
    #             self._timeline.stop()
    #         else:
    #             curr_vel = float(og.DataView.get(odom_velocity)[0])
    #             self.assertAlmostEqual(curr_vel, forward_velocity, delta=8e-2)
    #             self.assertAlmostEqual(
    #                 curr_vel, (self.dc.get_rigid_body_angular_velocity(l_wheel)[1]) * 0.24, delta=5e-1
    #             )
    #             print(self.dc.get_rigid_body_angular_velocity(l_wheel)[1] * 0.24)
    #             print("correct forward velocity: " + str(forward_velocity))

    #         await omni.kit.app.get_app().next_update_async()

    #     self._timeline.stop()

    #     pass
