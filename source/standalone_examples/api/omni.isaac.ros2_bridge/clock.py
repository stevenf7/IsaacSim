# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import time
import carb
from omni.isaac.kit import SimulationApp


# Example ROS2 bridge sample showing rclpy and rosclock interaction
simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": True})
import omni
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core import SimulationContext

# enable ROS2 bridge extension
enable_extension("omni.isaac.ros2_bridge")

simulation_app.update()
# Note that this is not the system level rclpy, but one compiled for omniverse
import rclpy
from rosgraph_msgs.msg import Clock

rclpy.init()
# create a clock using sim time
result, prim = omni.kit.commands.execute(
    "ROSBridgeCreateClock", path="/ROS_Clock_Sim", clock_topic="/sim_time", sim_time=True
)
# create a clock using system time
result, prim = omni.kit.commands.execute(
    "ROSBridgeCreateClock", path="/ROS_Clock_System", clock_topic="/system_time", sim_time=False
)
# create a clock which we will publish manually, set enabled to false to make it manually controlled
result, prim = omni.kit.commands.execute(
    "ROSBridgeCreateClock", path="/ROS_Clock_Manual", clock_topic="/manual_time", sim_time=True, enabled=False
)
simulation_app.update()
simulation_app.update()

# Define ROS2 callbacks
def sim_clock_callback(data):
    print("sim time:", data.clock)


def system_clock_callback(data):
    print("system time:", data.clock)


def manual_clock_callback(data):
    print("manual stepped sim time:", data.clock)


# Create rclpy ndoe
node = rclpy.create_node("isaac_sim_test_gripper")

# create subscribers
sim_clock_sub = node.create_subscription(Clock, "sim_time", sim_clock_callback, 1)
system_clock_sub = node.create_subscription(Clock, "system_time", system_clock_callback, 1)
manual_clock_sub = node.create_subscription(Clock, "manual_time", manual_clock_callback, 1)

time.sleep(1.0)
# start simulation
simulation_context = SimulationContext(physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0, stage_units_in_meters=0.01)
simulation_context.start_simulation()
simulation_context.play()

# perform a fixed number of steps with fixed step size
for frame in range(20):

    # publish manual clock every 10 frames
    if frame % 2 == 0:
        result, status = omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_Clock_Manual")
        simulation_context.render()  # This updates rendering/app loop which calls the system and sim clocks

    simulation_context.step(render=False)  # runs with a non-realtime clock
    rclpy.spin_once(node, timeout_sec=0.0)  # Spin node once
    # This sleep is to make this sample run a bit more deterministically for the subscriber callback
    # In general this sleep is not needed
    time.sleep(0.1)

# perform a fixed number of steps with realtime clock
for frame in range(20):

    # publish manual clock every 10 frames
    if frame % 2 == 0:
        result, status = omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_Clock_Manual")

    simulation_app.update()  # runs with a realtime clock
    rclpy.spin_once(node, timeout_sec=0.0)  # Spin node once
    # This sleep is to make this sample run a bit more deterministically for the subscriber callback
    # In general this sleep is not needed
    time.sleep(0.1)

# shutdown
rclpy.shutdown()
simulation_context.stop()
simulation_app.close()
