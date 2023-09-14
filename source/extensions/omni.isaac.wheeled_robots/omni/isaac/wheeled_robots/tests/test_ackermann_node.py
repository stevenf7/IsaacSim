# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import numpy as np
import omni.graph.core as og
import omni.graph.core.tests as ogts
import omni.kit.test
import omni.timeline


class TestAckermannSteeringNode(ogts.OmniGraphTestCase):
    async def setUp(self):
        """Set up  test environment, to be torn down when done"""
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        # configurations are based on the forklift_c model
        self.turning_wheel_radius = 0.255
        self.track_width = 0.82
        self.wheel_base = 1.65
        self.max_wheel_velocity = 20  # rad / s
        self.max_wheel_turning_rotation = 60  # degrees (heading angle)

    # ----------------------------------------------------------------------
    async def tearDown(self):
        """Get rid of temporary data used by the test"""
        await omni.kit.stage_templates.new_stage_async()

    # ----------------------------------------------------------------------
    async def test_ackermann_steering_node_forward_left(self):
        lin_vel = 0
        accel = 1
        curvature = -0.3
        (test_diff_graph, [diff_node, playbacktick], _, _) = og.Controller.edit(
            {"graph_path": "/ActionGraph"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("AckermannSteering", "omni.isaac.wheeled_robots.AckermannSteering"),
                    ("OnTick", "omni.graph.action.OnTick"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("AckermannSteering.inputs:accel", accel),
                    ("AckermannSteering.inputs:curvature", curvature),
                    ("AckermannSteering.inputs:turningWheelRadius", self.turning_wheel_radius),
                    ("AckermannSteering.inputs:maxWheelVelocity", self.max_wheel_velocity),
                    ("AckermannSteering.inputs:trackWidth", self.track_width),
                    ("AckermannSteering.inputs:wheelBase", self.wheel_base),
                    ("AckermannSteering.inputs:invertCurvature", False),  # front wheel drive
                    ("AckermannSteering.inputs:maxWheelRotation", self.max_wheel_turning_rotation),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnTick.outputs:deltaSeconds", "AckermannSteering.inputs:DT"),
                    ("OnTick.outputs:tick", "AckermannSteering.inputs:execIn"),
                ],
            },
        )
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        # compute ackermann steering angle
        delta_ack = np.arcsin(self.wheel_base * curvature * -1)  # -1 for front wheel drive
        left_wheel = np.rad2deg(
            np.arctan(
                (self.wheel_base * np.tan(delta_ack)) / (self.wheel_base + 0.5 * self.track_width * np.tan(delta_ack))
            )
        )
        right_wheel = np.rad2deg(
            np.arctan(
                (self.wheel_base * np.tan(delta_ack)) / (self.wheel_base - 0.5 * self.track_width * np.tan(delta_ack))
            )
        )

        for i in range(60):
            await omni.kit.app.get_app().next_update_async()
            og.Controller.attribute("/ActionGraph/AckermannSteering.inputs:linearVelocity").set([0, lin_vel, 0])
            lin_vel = (
                lin_vel + og.Controller(og.Controller.attribute("outputs:deltaSeconds", playbacktick)).get() * accel
            )

        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:wheelRotationVelocity", diff_node)).get(),
            lin_vel / self.turning_wheel_radius,
            delta=0.5,
        )
        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(), left_wheel, delta=0.5
        )
        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(), right_wheel, delta=0.5
        )

    # ----------------------------------------------------------------------
    async def test_ackermann_steering_node_reverse_right(self):
        lin_vel = 0
        accel = -1
        curvature = 0.3
        (test_diff_graph, [diff_node, playbacktick], _, _) = og.Controller.edit(
            {"graph_path": "/ActionGraph"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("AckermannSteering", "omni.isaac.wheeled_robots.AckermannSteering"),
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("AckermannSteering.inputs:accel", accel),
                    ("AckermannSteering.inputs:curvature", curvature),
                    ("AckermannSteering.inputs:turningWheelRadius", self.turning_wheel_radius),
                    ("AckermannSteering.inputs:maxWheelVelocity", self.max_wheel_velocity),
                    ("AckermannSteering.inputs:trackWidth", self.track_width),
                    ("AckermannSteering.inputs:wheelBase", self.wheel_base),
                    ("AckermannSteering.inputs:invertCurvature", False),  # front wheel drive
                    ("AckermannSteering.inputs:maxWheelRotation", self.max_wheel_turning_rotation),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:deltaSeconds", "AckermannSteering.inputs:DT"),
                    ("OnPlaybackTick.outputs:tick", "AckermannSteering.inputs:execIn"),
                ],
            },
        )
        self._timeline.play()
        for i in range(60):
            await omni.kit.app.get_app().next_update_async()
            og.Controller.attribute("/ActionGraph/AckermannSteering.inputs:linearVelocity").set([0, lin_vel, 0])
            lin_vel = (
                lin_vel + og.Controller(og.Controller.attribute("outputs:deltaSeconds", playbacktick)).get() * accel
            )

        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:wheelRotationVelocity", diff_node)).get(),
            lin_vel / self.turning_wheel_radius,
            delta=0.5,
        )

        # should be negative values
        self.assertLess(og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(), 0)
        self.assertLess(og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(), 0)

    # ----------------------------------------------------------------------
    async def test_ackermann_steering_node_rwd_forward_left(self):
        accel = 1
        lin_vel = 0
        curvature = -0.3
        (test_diff_graph, [diff_node, playbacktick], _, _) = og.Controller.edit(
            {"graph_path": "/ActionGraph"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("AckermannSteering", "omni.isaac.wheeled_robots.AckermannSteering"),
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("AckermannSteering.inputs:accel", accel),
                    ("AckermannSteering.inputs:curvature", curvature),
                    ("AckermannSteering.inputs:turningWheelRadius", self.turning_wheel_radius),
                    ("AckermannSteering.inputs:maxWheelVelocity", self.max_wheel_velocity),
                    ("AckermannSteering.inputs:trackWidth", self.track_width),
                    ("AckermannSteering.inputs:wheelBase", self.wheel_base),
                    ("AckermannSteering.inputs:invertCurvature", True),  # rear wheel drive
                    ("AckermannSteering.inputs:maxWheelRotation", self.max_wheel_turning_rotation),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:deltaSeconds", "AckermannSteering.inputs:DT"),
                    ("OnPlaybackTick.outputs:tick", "AckermannSteering.inputs:execIn"),
                ],
            },
        )

        for i in range(60):
            await omni.kit.app.get_app().next_update_async()
            og.Controller.attribute("/ActionGraph/AckermannSteering.inputs:linearVelocity").set([0, lin_vel, 0])
            lin_vel = (
                lin_vel + og.Controller(og.Controller.attribute("outputs:deltaSeconds", playbacktick)).get() * accel
            )

        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:wheelRotationVelocity", diff_node)).get(),
            lin_vel / self.turning_wheel_radius,
            delta=0.5,
        )

        # rwd forward left is the same as fwd reverse right
        self.assertLess(og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(), 0)
        self.assertLess(og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(), 0)

    # ----------------------------------------------------------------------
    async def test_ackermann_steering_node_rwd_reverse_right(self):
        accel = -1
        lin_vel = 0
        curvature = 0.3
        (test_diff_graph, [diff_node, playbacktick], _, _) = og.Controller.edit(
            {"graph_path": "/ActionGraph"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("AckermannSteering", "omni.isaac.wheeled_robots.AckermannSteering"),
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("AckermannSteering.inputs:accel", accel),
                    ("AckermannSteering.inputs:curvature", curvature),
                    ("AckermannSteering.inputs:turningWheelRadius", self.turning_wheel_radius),
                    ("AckermannSteering.inputs:maxWheelVelocity", self.max_wheel_velocity),
                    ("AckermannSteering.inputs:trackWidth", self.track_width),
                    ("AckermannSteering.inputs:wheelBase", self.wheel_base),
                    ("AckermannSteering.inputs:invertCurvature", True),  # rear wheel drive
                    ("AckermannSteering.inputs:maxWheelRotation", self.max_wheel_turning_rotation),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:deltaSeconds", "AckermannSteering.inputs:DT"),
                    ("OnPlaybackTick.outputs:tick", "AckermannSteering.inputs:execIn"),
                ],
            },
        )

        for i in range(60):
            await omni.kit.app.get_app().next_update_async()
            og.Controller.attribute("/ActionGraph/AckermannSteering.inputs:linearVelocity").set([0, lin_vel, 0])
            lin_vel = (
                lin_vel + og.Controller(og.Controller.attribute("outputs:deltaSeconds", playbacktick)).get() * accel
            )

        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:wheelRotationVelocity", diff_node)).get(),
            lin_vel / self.turning_wheel_radius,
            delta=0.5,
        )

        # rwd reverse right is the same as fwd forward left
        self.assertGreater(og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(), 0)
        self.assertGreater(og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(), 0)

    # ----------------------------------------------------------------------
    async def test_ackermann_steering_node_curvatures(self):
        (test_diff_graph, [diff_node, playbacktick], _, _) = og.Controller.edit(
            {"graph_path": "/ActionGraph"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("AckermannSteering", "omni.isaac.wheeled_robots.AckermannSteering"),
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("AckermannSteering.inputs:accel", 0.0),
                    ("AckermannSteering.inputs:turningWheelRadius", self.turning_wheel_radius),
                    ("AckermannSteering.inputs:maxWheelVelocity", self.max_wheel_velocity),
                    ("AckermannSteering.inputs:trackWidth", self.track_width),
                    ("AckermannSteering.inputs:wheelBase", self.wheel_base),
                    ("AckermannSteering.inputs:invertCurvature", True),  # rear wheel drive
                    ("AckermannSteering.inputs:maxWheelRotation", self.max_wheel_turning_rotation),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:deltaSeconds", "AckermannSteering.inputs:DT"),
                    ("OnPlaybackTick.outputs:tick", "AckermannSteering.inputs:execIn"),
                ],
            },
        )

        og.Controller(og.Controller.attribute("inputs:curvature", diff_node)).set(0.2)

        await og.Controller.evaluate(test_diff_graph)

        rotations_2 = [
            og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(),
            og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(),
        ]

        og.Controller(og.Controller.attribute("inputs:curvature", diff_node)).set(0.4)

        await og.Controller.evaluate(test_diff_graph)

        rotations_4 = [
            og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(),
            og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(),
        ]

        # # compute steering angle
        # delta_ack = np.arcsin(self.wheel_base * 0.2)
        # left_wheel = np.rad2deg(np.arctan((self.wheel_base * np.tan(delta_ack))/(self.wheel_base + 0.5 * self.track_width * np.tan(delta_ack))))
        # right_wheel = np.rad2deg(np.arctan((self.wheel_base * np.tan(delta_ack))/(self.wheel_base - 0.5 * self.track_width * np.tan(delta_ack))))
        # print(f"left_wheel {left_wheel} right_wheel {right_wheel}")

        # delta_ack = np.arcsin(self.wheel_base * 0.4)
        # left_wheel = np.rad2deg(np.arctan((self.wheel_base * np.tan(delta_ack))/(self.wheel_base + 0.5 * self.track_width * np.tan(delta_ack))))
        # right_wheel = np.rad2deg(np.arctan((self.wheel_base * np.tan(delta_ack))/(self.wheel_base - 0.5 * self.track_width * np.tan(delta_ack))))
        # print(f"left_wheel {left_wheel} right_wheel {right_wheel}")

        self.assertLess(rotations_2[0], rotations_4[0])
        self.assertLess(rotations_2[1], rotations_4[1])
        self.assertNotAlmostEqual(rotations_2[0], rotations_4[0], delta=10)
        self.assertNotAlmostEqual(rotations_2[1], rotations_4[1], delta=10)

    # ----------------------------------------------------------------------
    async def test_ackermann_steering_node_maximums_forward(self):
        accel = 1000
        lin_vel = 0
        max_w = self.max_wheel_velocity
        max_r = self.max_wheel_turning_rotation

        (test_diff_graph, [diff_node, playbacktick], _, _) = og.Controller.edit(
            {"graph_path": "/ActionGraph"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("AckermannSteering", "omni.isaac.wheeled_robots.AckermannSteering"),
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("AckermannSteering.inputs:accel", accel),
                    ("AckermannSteering.inputs:curvature", 0.5),
                    ("AckermannSteering.inputs:turningWheelRadius", self.turning_wheel_radius),
                    ("AckermannSteering.inputs:maxWheelVelocity", max_w),
                    ("AckermannSteering.inputs:trackWidth", self.track_width),
                    ("AckermannSteering.inputs:wheelBase", self.wheel_base),
                    ("AckermannSteering.inputs:invertCurvature", True),
                    ("AckermannSteering.inputs:maxWheelRotation", max_r),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:deltaSeconds", "AckermannSteering.inputs:DT"),
                    ("OnPlaybackTick.outputs:tick", "AckermannSteering.inputs:execIn"),
                ],
            },
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        for i in range(60):
            await omni.kit.app.get_app().next_update_async()
            og.Controller.attribute("/ActionGraph/AckermannSteering.inputs:linearVelocity").set([0, lin_vel, 0])
            lin_vel = (
                lin_vel + og.Controller(og.Controller.attribute("outputs:deltaSeconds", playbacktick)).get() * accel
            )

        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:wheelRotationVelocity", diff_node)).get(), max_w, delta=0.5
        )
        self.assertLessEqual(og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(), max_r)
        self.assertLessEqual(og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(), max_r)

    # ----------------------------------------------------------------------
    async def test_ackermann_steering_node_maximums_reverse(self):
        accel = -1000
        lin_vel = 0
        curvature = -0.5
        max_w = self.max_wheel_velocity
        max_r = self.max_wheel_turning_rotation

        (test_diff_graph, [diff_node, playbacktick], _, _) = og.Controller.edit(
            {"graph_path": "/ActionGraph"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("AckermannSteering", "omni.isaac.wheeled_robots.AckermannSteering"),
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("AckermannSteering.inputs:accel", accel),
                    ("AckermannSteering.inputs:curvature", curvature),
                    ("AckermannSteering.inputs:turningWheelRadius", self.turning_wheel_radius),
                    ("AckermannSteering.inputs:maxWheelVelocity", max_w),
                    ("AckermannSteering.inputs:trackWidth", self.track_width),
                    ("AckermannSteering.inputs:wheelBase", self.wheel_base),
                    ("AckermannSteering.inputs:invertCurvature", True),
                    ("AckermannSteering.inputs:maxWheelRotation", max_r),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:deltaSeconds", "AckermannSteering.inputs:DT"),
                    ("OnPlaybackTick.outputs:tick", "AckermannSteering.inputs:execIn"),
                ],
            },
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        for i in range(60):
            await omni.kit.app.get_app().next_update_async()
            og.Controller.attribute("/ActionGraph/AckermannSteering.inputs:linearVelocity").set([0, lin_vel, 0])
            lin_vel = (
                lin_vel + og.Controller(og.Controller.attribute("outputs:deltaSeconds", playbacktick)).get() * accel
            )

        self.assertAlmostEqual(
            og.Controller(og.Controller.attribute("outputs:wheelRotationVelocity", diff_node)).get(), -max_w, delta=0.5
        )
        self.assertGreaterEqual(
            og.Controller(og.Controller.attribute("outputs:leftWheelAngle", diff_node)).get(), -max_r
        )
        self.assertGreaterEqual(
            og.Controller(og.Controller.attribute("outputs:rightWheelAngle", diff_node)).get(), -max_r
        )
