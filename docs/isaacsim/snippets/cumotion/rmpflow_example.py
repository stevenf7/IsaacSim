# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
================================================================================
⚠️  IMPORTANT: TUTORIAL EXTENSION MUST BE UPDATED IF THIS FILE IS MODIFIED  ⚠️
================================================================================

This file contains code snippets that are displayed in the cuMotion RMPflow
tutorial documentation. If you modify this file, you MUST also update the
corresponding tutorial extension at:
    source/extensions/isaacsim.robot_motion.cumotion.examples/isaacsim/robot_motion/cumotion/examples/rmp_flow/

The tutorial RST file is at:
    docs/isaacsim/cumotion/tutorial_rmpflow.rst

================================================================================
"""

"""
Complete example demonstrating RmpFlowController usage.

This example shows how to:
- Create and configure the RmpFlowController
- Use the controller with RobotState objects
- Update world state for dynamic environments
- Reset the controller
- Access cuMotion parameters
"""

# ============================================================================
# 1. Launch Simulation App
# ============================================================================
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

# Now we can import Isaac Sim modules
import isaacsim.core.experimental.utils.stage as stage_utils
import isaacsim.robot_motion.experimental.motion_generation as mg
import numpy as np
import omni.timeline
import warp as wp
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import Articulation, GeomPrim
from isaacsim.core.experimental.utils.stage import add_reference_to_stage
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot_motion.cumotion import (
    CumotionWorldInterface,
    RmpFlowController,
    load_cumotion_supported_robot,
)
from isaacsim.robot_motion.experimental.motion_generation import (
    ObstacleStrategy,
    SceneQuery,
    TrackableApi,
    WorldBinding,
)
from isaacsim.storage.native import get_assets_root_path


# ============================================================================
# 2. Setting Up the Controller
# ============================================================================
def setup_controller(world_binding):
    """Create and configure the RmpFlowController."""
    # Note: In this snippet, we assume the robot is already loaded in the stage
    # For the standalone example, the robot is loaded in main() before calling this function
    # Load robot configuration for supported robots
    cumotion_robot = load_cumotion_supported_robot("franka")
    articulation = Articulation("/panda")

    # <start-setup-controller-snippet>
    # Get robot joint and site names
    robot_joint_space = articulation.dof_names
    robot_site_space = cumotion_robot.robot_description.tool_frame_names()
    tool_frame = robot_site_space[0]

    # Create RMPflow controller
    controller = RmpFlowController(
        cumotion_robot=cumotion_robot,
        cumotion_world_interface=world_binding.get_world_interface(),
        robot_joint_space=robot_joint_space,
        robot_site_space=robot_site_space,
        tool_frame=tool_frame,
    )
    # <end-setup-controller-snippet>

    return controller, cumotion_robot, articulation


# ============================================================================
# 3. Helper Functions for RobotState Creation
# ============================================================================
def get_estimated_state(articulation):
    """Get the current robot state as a RobotState."""
    # <start-get-estimated-state-snippet>
    # Get current robot state
    robot_joint_space = articulation.dof_names

    # Create estimated state (current robot state)
    estimated_state = mg.RobotState(
        joints=mg.JointState.from_name(
            robot_joint_space=robot_joint_space,
            positions=(robot_joint_space, articulation.get_dof_positions()),
            velocities=(robot_joint_space, articulation.get_dof_velocities()),
        )
    )
    # <end-get-estimated-state-snippet>

    return estimated_state


def create_setpoint_state(cumotion_robot, target_object):
    """Create a setpoint state from a target object."""
    # <start-create-setpoint-state-snippet>
    # Create setpoint with target end-effector pose
    tool_frame_name = cumotion_robot.robot_description.tool_frame_names()[0]
    robot_site_space = cumotion_robot.robot_description.tool_frame_names()

    # Get target pose (example: from a target object)
    target_positions, target_orientations = target_object.get_world_poses()

    setpoint_state = mg.RobotState(
        sites=mg.SpatialState.from_name(
            spatial_space=robot_site_space,
            positions=([tool_frame_name], target_positions),
            orientations=([tool_frame_name], target_orientations),
        ),
    )
    # <end-create-setpoint-state-snippet>

    return setpoint_state


# ============================================================================
# 4. Running the Controller
# ============================================================================
def run_controller(controller, cumotion_robot, articulation, world_binding, target_object, t):
    """Run the controller at the given clock time."""
    # Update world state before running controller
    world_binding.get_world_interface().update_world_to_robot_root_transforms(articulation.get_world_poses())
    world_binding.synchronize_transforms()

    # Get robot states
    estimated_state = get_estimated_state(articulation)
    setpoint_state = create_setpoint_state(cumotion_robot, target_object)

    # <start-run-controller-snippet>
    # Get desired state from controller (t is the clock time, not a time step)
    desired_state = controller.forward(estimated_state, setpoint_state, t)

    # Apply action to articulation
    if desired_state is not None and desired_state.joints.positions is not None:
        articulation.set_dof_position_targets(
            positions=desired_state.joints.positions,
            dof_indices=desired_state.joints.position_indices,
        )
    # <end-run-controller-snippet>


# ============================================================================
# 5. Updating World State
# ============================================================================
def update_world_state(world_binding, articulation):
    """Update world binding to track moving obstacles and robot base movements."""
    # <start-update-world-state-snippet>
    # Update robot base transform
    world_binding.get_world_interface().update_world_to_robot_root_transforms(articulation.get_world_poses())

    # Synchronize transforms (updates all obstacles and world state)
    world_binding.synchronize_transforms()
    # <end-update-world-state-snippet>


# ============================================================================
# 4. Resetting the Controller
# ============================================================================
def reset_controller(controller, cumotion_robot, articulation, target_object, t=0.0):
    """Reset the controller before first use or when starting a new task."""
    # Get robot states
    estimated_state = get_estimated_state(articulation)
    setpoint_state = create_setpoint_state(cumotion_robot, target_object)

    # <start-reset-controller-snippet>
    # Reset the controller - must return True before forward can be called
    success = controller.reset(estimated_state, setpoint_state, t=t)
    if not success:
        raise RuntimeError("Controller reset failed. Check that estimated_state contains all required joint positions.")
    # <end-reset-controller-snippet>


# ============================================================================
# 7. Accessing cuMotion Parameters
# ============================================================================
def access_parameters(controller):
    """Demonstrate accessing and modifying cuMotion parameters."""
    # <start-access-parameters-snippet>
    # Get the underlying cuMotion config
    rmpflow_config = controller.get_rmp_flow_config()

    # Modify parameters using set_param
    rmpflow_config.set_param("cspace_target_rmp/damping_gain", 0.9)
    # <end-access-parameters-snippet>


# ============================================================================
# 7. Main Example
# ============================================================================
def main():
    """Run the complete example."""

    # Setup scene
    stage_utils.create_new_stage(template="default stage")
    stage_utils.set_stage_units(meters_per_unit=1.0)

    # Load robot
    robot_prim_path = "/panda"
    path_to_robot_usd = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
    add_reference_to_stage(path_to_robot_usd, robot_prim_path)
    articulation = Articulation(robot_prim_path)

    # Create target object
    target_object = Cube("/World/target", sizes=0.04, positions=[0.5, 0.0, 0.7])
    GeomPrim("/World/target", apply_collision_apis=True)

    # Create obstacle
    obstacle_path = "/World/obstacle"
    Cube(obstacle_path, sizes=0.05, positions=[0.4, 0.0, 0.65])
    GeomPrim(obstacle_path, apply_collision_apis=True)

    # Create world binding (simplified setup)
    scene_query = SceneQuery()
    robot_base_positions, robot_base_orientations = articulation.get_world_poses()
    search_origin = robot_base_positions.numpy()[0] if robot_base_positions.shape[0] > 0 else [0.0, 0.0, 0.0]
    objects = scene_query.get_prims_in_aabb(
        search_box_origin=search_origin,
        search_box_minimum=[-10.0, -10.0, -10.0],
        search_box_maximum=[10.0, 10.0, 10.0],
        tracked_api=TrackableApi.PHYSICS_COLLISION,
        exclude_prim_paths=[robot_prim_path],
    )
    obstacle_strategy = ObstacleStrategy()
    world_binding = WorldBinding(
        world_interface=CumotionWorldInterface(),
        obstacle_strategy=obstacle_strategy,
        tracked_prims=objects,
        tracked_collision_api=TrackableApi.PHYSICS_COLLISION,
    )
    world_binding.initialize()
    world_binding.get_world_interface().update_world_to_robot_root_transforms(
        poses=(robot_base_positions, robot_base_orientations)
    )
    world_binding.synchronize_transforms()

    # Setup controller
    controller, cumotion_robot, articulation = setup_controller(world_binding)

    # Test parameter access
    access_parameters(controller)

    # Initialize physics
    SimulationManager.set_physics_dt(1.0 / 60.0)

    # Run controller for a few steps
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    simulation_app.update()

    # Test reset
    reset_controller(controller, cumotion_robot, articulation, target_object, t=0.0)

    # Run controller for a limited number of steps
    physics_dt = 1.0 / 60.0
    t = 0.0
    for _ in range(10):  # Run for 10 steps
        simulation_app.update()
        update_world_state(world_binding, articulation)
        t += physics_dt
        run_controller(controller, cumotion_robot, articulation, world_binding, target_object, t)

    timeline.pause()
    print("RMPflow example complete!")


if __name__ == "__main__":
    main()
    simulation_app.close()
