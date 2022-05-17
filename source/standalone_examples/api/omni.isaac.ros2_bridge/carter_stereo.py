# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from omni.isaac.kit import SimulationApp
import argparse

parser = argparse.ArgumentParser(description="Generate Occluded and Unoccluded data")
parser.add_argument("--test", action="store_true")
args, unknown = parser.parse_known_args()

# Example ROS2 bridge sample showing manual control over messages
kit = SimulationApp({"renderer": "RayTracedLighting", "headless": False})
import omni
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core import SimulationContext
from pxr import Sdf

from omni.isaac.core.utils.extensions import enable_extension

# enable ROS2 bridge extension
enable_extension("omni.isaac.ros2_bridge")

# Locate assets root folder to load sample
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    kit.close()
    exit()

usd_path = assets_root_path + "/Isaac/Samples/ROS/Scenario/carter_warehouse_navigation.usd"
omni.usd.get_context().open_stage(usd_path, None)

# Wait two frames so that stage starts loading
kit.update()
kit.update()

print("Loading stage...")
from omni.isaac.core.utils.stage import is_stage_loading

while is_stage_loading():
    kit.update()
print("Loading Complete")

simulation_context = SimulationContext(stage_units_in_meters=1.0)

# Disable all ROS components so we can demonstrate publishing manually
# Otherwise, if a component is enabled, it will publish every timestep
omni.kit.commands.execute(
    "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Camera_Stereo_Right.enabled"), value=False, prev=None
)
omni.kit.commands.execute(
    "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Camera_Stereo_Left.enabled"), value=False, prev=None
)
omni.kit.commands.execute(
    "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Lidar.enabled"), value=False, prev=None
)
omni.kit.commands.execute(
    "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_DifferentialBase.enabled"), value=False, prev=None
)
omni.kit.commands.execute(
    "ChangeProperty",
    prop_path=Sdf.Path("/World/Carter_ROS/ROS_Carter_Sensors_Broadcaster.enabled"),
    value=False,
    prev=None,
)
omni.kit.commands.execute(
    "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Carter_Broadcaster.enabled"), value=False, prev=None
)
omni.kit.commands.execute("ChangeProperty", prop_path=Sdf.Path("/World/ROS_Clock.enabled"), value=False, prev=None)
simulation_context.play()
simulation_context.step()
# Tick all of the components once to make sure all of the ROS2 nodes are initialized
# For cameras this also handles viewport initialization etc.
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Camera_Stereo_Right")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Camera_Stereo_Left")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Lidar")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_DifferentialBase")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Carter_Sensors_Broadcaster")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Carter_Broadcaster")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/ROS_Clock")
# Simulate for one second to warm up sim and let everything settle
for frame in range(60):
    simulation_context.step()

# Dock the second camera window
right_viewport = omni.ui.Workspace.get_window("Viewport")
left_viewport = omni.ui.Workspace.get_window("Viewport 2")
if right_viewport is not None and left_viewport is not None:
    left_viewport.dock_in(right_viewport, omni.ui.DockPosition.LEFT)
right_viewport = None
left_viewport = None

# Create a rostopic to publish message to spin robot in place
# Note that this is not the system level rclpy, but one compiled for omniverse

import rclpy

rclpy.init()

from geometry_msgs.msg import Twist

node = rclpy.create_node("carter_stereo")
publisher = node.create_publisher(Twist, "cmd_vel", 10)

frame = 0
while kit.is_running():
    # Run with a fixed step size
    simulation_context.step()
    # Publish clock every frame
    omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/ROS_Clock")
    # publish TF and Lidar every 2 frames
    if frame % 2 == 0:
        omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Lidar")
        omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_DifferentialBase")
        omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Carter_Sensors_Broadcaster")
        omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Carter_Broadcaster")
        # because we only tick the differential base component every two frames, we can also publish the ROS message at the same rate
        message = Twist()
        message.angular.z = 0.2  # spin in place
        publisher.publish(message)
    # Publish cameras every 15 frames
    if frame % 15 == 0:
        omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Camera_Stereo_Right")
        omni.kit.commands.execute("Ros2BridgeTickComponent", path="/World/Carter_ROS/ROS_Camera_Stereo_Left")
    if args.test and frame > 120:
        break
    frame = frame + 1
node.destroy_node()
rclpy.shutdown()
simulation_context.stop()
kit.close()
