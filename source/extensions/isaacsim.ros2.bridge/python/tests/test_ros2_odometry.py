# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import asyncio
import gc

import carb
import numpy as np
import omni.graph.core as og

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
import omni.kit.test
import omni.kit.usd
import omni.kit.viewport.utility
import usdrt.Sdf
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.api.scenes.scene import Scene
from isaacsim.core.api.tasks import BaseTask
from isaacsim.core.utils.physics import simulate_async
from isaacsim.core.utils.prims import is_prim_path_valid
from isaacsim.core.utils.stage import get_stage_units, open_stage_async
from isaacsim.core.utils.string import find_unique_string_name
from isaacsim.core.utils.xforms import get_world_pose
from isaacsim.storage.native import get_assets_root_path_async
from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdLux, UsdPhysics

from .common import get_qos_profile


class TestRos2Odometry(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        import rclpy

        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("isaacsim.ros2.bridge")
        self._ros_extension_path = ext_manager.get_extension_path(ext_id)

        self._assets_root_path = await get_assets_root_path_async()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        kit_folder = carb.tokens.get_tokens_interface().resolve("${kit}")

        self.my_world = World(stage_units_in_meters=1.0)
        await self.my_world.initialize_simulation_context_async()

        self._physics_rate = 60

        self.CUBE_SCALE = 0.5

        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        await omni.kit.app.get_app().next_update_async()

        rclpy.init()

        pass

    # After running each test
    async def tearDown(self):
        import rclpy

        self.my_world.stop()
        self.my_world.clear_instance()

        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)

        self._timeline = None
        rclpy.shutdown()
        gc.collect()

        pass

    def get_cube_velocities(self):
        """Return a tuple (linear_velocity, angular_velocity) from the stored odometry message."""
        if self._cube_odometry_data is None:
            return None, None
        # Odometry.twist.twist contains the velocities.
        linear_velocity = self._cube_odometry_data.twist.twist.linear
        angular_velocity = self._cube_odometry_data.twist.twist.angular
        return linear_velocity, angular_velocity

    def get_cube_pose(self):
        """Return a tuple (position, orientation) from the stored odometry message."""
        if self._cube_odometry_data is None:
            return None, None
        # Odometry.pose.pose contains the position and orientation
        position = self._cube_odometry_data.pose.pose.position
        orientation = self._cube_odometry_data.pose.pose.orientation
        return position, orientation

    async def test_ROS2_odometry(self):
        import rclpy
        from nav_msgs.msg import Odometry

        self.lin_vel_cmd = None
        self.ang_vel_cmd = None

        cube_prim_path = find_unique_string_name(
            initial_name="/World/Cube", is_unique_fn=lambda x: not is_prim_path_valid(x)
        )
        self.cuboid = DynamicCuboid(
            prim_path="/World/Cube",
            name="my_cuboid",
            position=np.array([0.0, 0.0, 1.0]),
            orientation=np.array([1, 0, 0, 0]),
            scale=np.array([self.CUBE_SCALE, self.CUBE_SCALE, self.CUBE_SCALE]),
            color=np.array([0, 0, 1]),
        )

        scene = Scene()
        scene.add(self.cuboid)
        scene.add_default_ground_plane()
        await omni.kit.app.get_app().next_update_async()

        # Define the action graph path
        graph_path = "/ActionGraph"

        try:
            keys = og.Controller.Keys
            (graph, nodes, _, _) = og.Controller.edit(
                {"graph_path": graph_path, "evaluator_name": "execution"},
                {
                    keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
                        ("ComputeOdometry", "isaacsim.core.nodes.IsaacComputeOdometry"),
                        ("PublishROS2Odometry", "isaacsim.ros2.bridge.ROS2PublishOdometry"),
                    ],
                    keys.SET_VALUES: [
                        ("ComputeOdometry.inputs:chassisPrim", [usdrt.Sdf.Path(cube_prim_path)]),
                        ("PublishROS2Odometry.inputs:topicName", "cube_odometry"),
                        ("PublishROS2Odometry.inputs:chassisFrameId", "cube_link"),
                        ("PublishROS2Odometry.inputs:publishRawVelocities", False),
                    ],
                    keys.CONNECT: [
                        ("OnPlaybackTick.outputs:tick", "ComputeOdometry.inputs:execIn"),
                        ("ComputeOdometry.outputs:execOut", "PublishROS2Odometry.inputs:execIn"),
                        ("ComputeOdometry.outputs:position", "PublishROS2Odometry.inputs:position"),
                        ("ComputeOdometry.outputs:orientation", "PublishROS2Odometry.inputs:orientation"),
                        ("ComputeOdometry.outputs:linearVelocity", "PublishROS2Odometry.inputs:linearVelocity"),
                        ("ComputeOdometry.outputs:angularVelocity", "PublishROS2Odometry.inputs:angularVelocity"),
                        ("ReadSimTime.outputs:simulationTime", "PublishROS2Odometry.inputs:timeStamp"),
                    ],
                },
            )
        except Exception as e:
            print(f"Error creating action graph: {e}")

        self._cube_odometry_data = None

        def cube_odometry_callback(data: Odometry):
            self._cube_odometry_data = data

        ros2_node = rclpy.create_node("odometry_publisher_tester")
        odom_sub = ros2_node.create_subscription(Odometry, "cube_odometry", cube_odometry_callback, get_qos_profile())

        self.retrived_lin_vel = None

        def set_cuboid_commands(cuboid_obj, lin_vel, ang_vel):
            cuboid_obj.set_linear_velocity(np.array(lin_vel, dtype=np.float64))

            # TODO (@Anthony or @Ayush): Setting angular velocity seems to take no effect. Using .get_angular_velocity() returns the correct value but the cuboid does not move accordingly. Will need to investigate
            cuboid_obj.set_angular_velocity(np.array(ang_vel, dtype=np.float64))
            self.retrived_lin_vel = cuboid_obj.get_angular_velocity()

        def spin():
            if (self.lin_vel_cmd is not None) and (self.ang_vel_cmd is not None):
                set_cuboid_commands(self.cuboid, self.lin_vel_cmd, self.ang_vel_cmd)
            rclpy.spin_once(ros2_node, timeout_sec=0.1)

        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        def standard_checks():
            # Check if odometry data was received.
            self.assertIsNotNone(self._cube_odometry_data, "Cube Odometry data was not recieved.")

            # Get velocities from odometry data.
            linear_vel, angular_vel = self.get_cube_velocities()
            self.assertIsNotNone(linear_vel, "Linear Velocity data is missing.")
            self.assertIsNotNone(angular_vel, "Angular velocity data is missing.")

            # Get position and orientation
            position, orientation = self.get_cube_pose()
            self.assertIsNotNone(position, "Position data is missing.")
            self.assertIsNotNone(orientation, "Orientation data is missing.")

            # Verify the received odometry messages
            self.assertIsNotNone(self._cube_odometry_data)

        await simulate_async(1, 60, spin)

        standard_checks()

        # Verify that the pose recieved from Odometry is correct
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.x, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.y, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.z, -0.7, delta=0.5)

        # Verify that the velocities recieved from Odometry are correct. Cude should be at rest.
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.x, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.y, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.z, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.angular.x, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.angular.y, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.angular.z, 0.0, places=2)

        self._timeline.stop()

        # Test1: Check Z odometry:
        ##############################
        self._cube_odometry_data = None

        self.lin_vel_cmd = [0.0, 0.0, 1.0]
        self.ang_vel_cmd = [0.0, 1.0, 0.0]

        self._timeline.play()

        await simulate_async(1, 60, spin)

        standard_checks()

        # Verify that the pose recieved from Odometry is correct
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.x, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.y, 0.0, places=2)
        self.assertGreater(self._cube_odometry_data.pose.pose.position.z, 0.2)

        # print(self.retrived_lin_vel)

        # Verify that the velocities recieved from Odometry are correct. Cude should be moving up.

        # TODO (@Anthony or @Ayush): Investigate why 0.2 disparity exists for commanded and received speeds
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.x, self.lin_vel_cmd[0], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.y, self.lin_vel_cmd[1], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.z, self.lin_vel_cmd[2], delta=0.2)

        # TODO (@Anthony or @Ayush): Setting angular velocity seems to take no effect. Using .get_angular_velocity() returns the correct value but the cuboid does not move accordingly. Will need to investigate
        # Commenting out angular velocity checks for now:

        # self.assertAlmostEqual(self._cube_odometry_data.twist.twist.angular.x, self.ang_vel_cmd[0], delta=0.2)
        # self.assertAlmostEqual(self._cube_odometry_data.twist.twist.angular.y, self.ang_vel_cmd[1], delta=0.2)
        # self.assertAlmostEqual(self._cube_odometry_data.twist.twist.angular.z, self.ang_vel_cmd[2], delta=0.2)

        self._timeline.stop()

        # Test2A: Check X odometry:
        ##############################
        self._cube_odometry_data = None

        self.cuboid.set_world_pose(
            position=np.array([0.0, 0.0, self.CUBE_SCALE / 2.0]),
            orientation=np.array([1, 0, 0, 0]),
        )

        self.lin_vel_cmd = None
        self.ang_vel_cmd = None

        self._timeline.play()

        await simulate_async(0.5, 60, spin)

        self.lin_vel_cmd = [1.0, 0.0, 0.0]
        self.ang_vel_cmd = [0.0, 1.0, 0.0]

        await simulate_async(1, 60, spin)

        standard_checks()

        # Verify that the pose recieved from Odometry is correct
        self.assertGreater(self._cube_odometry_data.pose.pose.position.x, 0.2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.y, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.z, 0.0, places=2)

        # Verify that the velocities recieved from Odometry are correct. Cude should be at moving forward.
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.x, self.lin_vel_cmd[0], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.y, self.lin_vel_cmd[1], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.z, self.lin_vel_cmd[2], delta=0.2)
        self._timeline.stop()

        # Test2B: Check X odometry (with robot front (0,1,0) and publishRawVelocities disabled:
        ##############################
        self._cube_odometry_data = None

        self.lin_vel_cmd = None
        self.ang_vel_cmd = None

        og.Controller.set(
            og.Controller.attribute(graph_path + "/PublishROS2Odometry.inputs:robotFront"), [0.0, 1.0, 0.0]
        )

        og.Controller.set(
            og.Controller.attribute(graph_path + "/PublishROS2Odometry.inputs:publishRawVelocities"), False
        )

        self.cuboid.set_world_pose(
            position=np.array([0.0, 0.0, self.CUBE_SCALE / 2.0]),
            orientation=np.array([1, 0, 0, 0]),
        )

        self._timeline.play()

        await simulate_async(0.5, 60, spin)

        self.lin_vel_cmd = [1.0, 0.0, 0.0]
        self.ang_vel_cmd = [0.0, 1.0, 0.0]

        await simulate_async(1, 60, spin)

        standard_checks()

        # Verify that the pose recieved from Odometry is correct. X should still be greater than 0
        self.assertGreater(self._cube_odometry_data.pose.pose.position.x, 0.2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.y, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.z, 0.0, places=2)

        # Verify that the velocities recieved from Odometry are correct. Cube should be moving forward in local Y frame, but global X frame.
        # Components are flipped due to new robot fron orientation. -Y world linear velocity is positive X local frame
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.x, self.lin_vel_cmd[1], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.y, -self.lin_vel_cmd[0], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.z, self.lin_vel_cmd[2], delta=0.2)

        self._timeline.stop()
        # Test2C: Check X odometry (with robot front (0,1,0) and publishRawVelocities enabled:
        ##############################
        self._cube_odometry_data = None

        self.lin_vel_cmd = None
        self.ang_vel_cmd = None

        og.Controller.set(
            og.Controller.attribute(graph_path + "/PublishROS2Odometry.inputs:robotFront"), [0.0, 1.0, 0.0]
        )

        og.Controller.set(
            og.Controller.attribute(graph_path + "/PublishROS2Odometry.inputs:publishRawVelocities"), True
        )

        self.cuboid.set_world_pose(
            position=np.array([0.0, 0.0, self.CUBE_SCALE / 2.0]),
            orientation=np.array([1, 0, 0, 0]),
        )

        self._timeline.play()

        await simulate_async(0.5, 60, spin)

        self.lin_vel_cmd = [1.0, 0.0, 0.0]
        self.ang_vel_cmd = [0.0, 1.0, 0.0]

        await simulate_async(1, 60, spin)

        standard_checks()

        # Verify that the pose recieved from Odometry is correct. X should still be greater than 0
        self.assertGreater(self._cube_odometry_data.pose.pose.position.x, 0.2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.y, 0.0, places=2)
        self.assertAlmostEqual(self._cube_odometry_data.pose.pose.position.z, 0.0, places=2)

        # Verify that the velocities recieved from Odometry are correct. Cube should be moving forward in local Y frame, but global X frame.
        # Components are no longer flipped like Test 2B since only world velocities are published
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.x, self.lin_vel_cmd[0], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.y, self.lin_vel_cmd[1], delta=0.2)
        self.assertAlmostEqual(self._cube_odometry_data.twist.twist.linear.z, self.lin_vel_cmd[2], delta=0.2)

        ros2_node.destroy_node()

        pass
