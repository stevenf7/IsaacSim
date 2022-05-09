# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
import sys
import carb
from omni.isaac.kit import SimulationApp

HOSPITAL_USD_PATH = "/Samples/ROS/Scenario/multiple_robot_carter_hospital_navigation.usd"
OFFICE_USD_PATH = "/Samples/ROS/Scenario/multiple_robot_carter_office_navigation.usd"

# Default environment: Hospital
ENV_USD_PATH = HOSPITAL_USD_PATH

if len(sys.argv) > 1:

    if sys.argv[1] == "office":
        # Choosing Office environment
        ENV_USD_PATH = OFFICE_USD_PATH

    elif sys.argv[1] != "hospital":
        carb.log_warn("Environment name is invalid. Choosing default Hospital environment.")
else:
    carb.log_warn("Environment name not specified. Choosing default Hospital environment.")


CONFIG = {"renderer": "RayTracedLighting", "headless": False}

# Example ROS bridge sample demonstrating the manual loading of Multiple Robot Navigation scenario
simulation_app = SimulationApp(CONFIG)
import omni
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import viewports, stage, extensions, prims, rotations, nucleus
from pxr import Sdf

# enable ROS bridge extension
ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_manager.set_extension_enabled_immediate("omni.isaac.ros_bridge", True)

# Locate assets root folder to load sample
assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

usd_path = assets_root_path + ENV_USD_PATH
omni.usd.get_context().open_stage(usd_path, None)
simulation_context = SimulationContext(stage_units_in_meters=1.0)

simulation_app.update()

# Disable all ROS components so we can demonstrate publishing manually
# Otherwise, if a component is enabled, it will publish every timestep

omni.kit.commands.execute("ChangeProperty", prop_path=Sdf.Path("/World/ROS_Clock.enabled"), value=False, prev=None)


def disable_carter_ros_components(robot_num):
    omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=Sdf.Path(f"/World/Carter_ROS_{robot_num}/ROS_Camera_Stereo_Right.enabled"),
        value=False,
        prev=None,
    )
    omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=Sdf.Path(f"/World/Carter_ROS_{robot_num}/ROS_Camera_Stereo_Left.enabled"),
        value=False,
        prev=None,
    )
    omni.kit.commands.execute(
        "ChangeProperty", prop_path=Sdf.Path(f"/World/Carter_ROS_{robot_num}/ROS_Lidar.enabled"), value=False, prev=None
    )
    omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=Sdf.Path(f"/World/Carter_ROS_{robot_num}/ROS_DifferentialBase.enabled"),
        value=False,
        prev=None,
    )
    omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=Sdf.Path(f"/World/Carter_ROS_{robot_num}/ROS_Carter_Sensors_Broadcaster.enabled"),
        value=False,
        prev=None,
    )
    omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=Sdf.Path(f"/World/Carter_ROS_{robot_num}/ROS_Carter_Broadcaster.enabled"),
        value=False,
        prev=None,
    )


disable_carter_ros_components(1)
disable_carter_ros_components(2)
disable_carter_ros_components(3)

simulation_context.start_simulation()
simulation_context.play()

# Tick all of the components once to make sure all of the ROS nodes are initialized
omni.kit.commands.execute("RosBridgeTickComponent", path="/World/ROS_Clock")


def tick_carter_ros_components(robot_num):
    omni.kit.commands.execute("RosBridgeTickComponent", path=f"/World/Carter_ROS_{robot_num}/ROS_Lidar")
    omni.kit.commands.execute("RosBridgeTickComponent", path=f"/World/Carter_ROS_{robot_num}/ROS_DifferentialBase")
    omni.kit.commands.execute(
        "RosBridgeTickComponent", path=f"/World/Carter_ROS_{robot_num}/ROS_Carter_Sensors_Broadcaster"
    )
    omni.kit.commands.execute("RosBridgeTickComponent", path=f"/World/Carter_ROS_{robot_num}/ROS_Carter_Broadcaster")
    omni.kit.commands.execute("RosBridgeTickComponent", path=f"/World/Carter_ROS_{robot_num}/ROS_Camera_Stereo_Left")


tick_carter_ros_components(1)
tick_carter_ros_components(2)
tick_carter_ros_components(3)

simulation_app.update()

# Dock the second and third camera window
carter1_viewport = omni.ui.Workspace.get_window("Viewport")
carter2_viewport = omni.ui.Workspace.get_window("Viewport 2")
carter3_viewport = omni.ui.Workspace.get_window("Viewport 3")
if carter1_viewport is not None and carter2_viewport is not None and carter3_viewport is not None:
    carter2_viewport.dock_in(carter1_viewport, omni.ui.DockPosition.RIGHT, 2 / 3.0)
    carter3_viewport.dock_in(carter2_viewport, omni.ui.DockPosition.RIGHT, 0.5)

while simulation_app.is_running():
    # Run with a fixed step size
    simulation_context.step(render=True)

    omni.kit.commands.execute("RosBridgeTickComponent", path="/World/ROS_Clock")
    tick_carter_ros_components(1)
    tick_carter_ros_components(2)
    tick_carter_ros_components(3)

simulation_context.stop()
simulation_app.close()
