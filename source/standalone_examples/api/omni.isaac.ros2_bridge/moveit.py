# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from omni.isaac.kit import SimulationApp
import numpy as np
import sys

FRANKA_STAGE_PATH = "/Franka"
FRANKA_USD_PATH = "/Robots/Franka/franka_alt_fingers.usd"
BACKGROUND_STAGE_PATH = "/background"
BACKGROUND_USD_PATH = "/Environments/Simple_Room/simple_room.usd"

CONFIG = {"renderer": "RayTracedLighting", "headless": False}

# Example ROS2 bridge sample demonstrating the manual loading of stages
# and creation of ROS components
simulation_app = SimulationApp(CONFIG)
import omni
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import viewports, stage, extensions, prims, rotations, nucleus
from pxr import Gf

# enable ROS2 bridge extension
extensions.enable_extension("omni.isaac.ros2_bridge")

simulation_context = SimulationContext(stage_units_in_meters=0.01)

# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

# Preparing stage
viewports.set_camera_view(eye=np.array([120, 120, 80]), target=np.array([0, 0, 50]))

# Loading the simple_room environment
stage.add_reference_to_stage(assets_root_path + BACKGROUND_USD_PATH, BACKGROUND_STAGE_PATH)

# Loading the franka robot USD
prims.create_prim(
    FRANKA_STAGE_PATH,
    "Xform",
    position=np.array([0, -64, 0]),
    orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 90)),
    usd_path=assets_root_path + FRANKA_USD_PATH,
)

simulation_app.update()

# Loading all ROS components initially as disabled so we can demonstrate publishing manually
# Otherwise, if a component is enabled, it will publish every timestep

# Load ROS Clock
omni.kit.commands.execute("ROSBridgeCreateClock", path="/ROS_Clock", enabled=False)

# Load Joint State
omni.kit.commands.execute(
    "ROSBridgeCreateJointState", path="/ROS_JointState", articulation_prim_rel=[FRANKA_STAGE_PATH], enabled=False
)

# Load Pose Tree
omni.kit.commands.execute(
    "ROSBridgeCreatePoseTree", path="/ROS_PoseTree", target_prims_rel=[FRANKA_STAGE_PATH], enabled=False
)

simulation_app.update()

# Tick all of the components once to make sure all of the ROS2 nodes are initialized
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_JointState")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_PoseTree")
omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_Clock")

# Simulate for one second to warm up sim and let everything settle
simulation_context.start_simulation()
simulation_context.play()
while simulation_app.is_running():

    # Run with a fixed step size
    simulation_context.step(render=True)

    # Publish clock, TF and JointState each frame
    omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_Clock")
    omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_JointState")
    omni.kit.commands.execute("Ros2BridgeTickComponent", path="/ROS_PoseTree")

simulation_context.stop()
simulation_app.close()
