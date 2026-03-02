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

This file contains code snippets that are displayed in the cuMotion Trajectory Optimizer
tutorial documentation. If you modify this file, you MUST also update the
corresponding tutorial extension at:
    source/extensions/isaacsim.robot_motion.cumotion.examples/isaacsim/robot_motion/cumotion/examples/trajectory_optimizer/

The tutorial RST file is at:
    docs/isaacsim/cumotion/tutorial_trajectory_optimizer.rst

================================================================================
"""

"""
Complete example demonstrating TrajectoryOptimizer usage.

This example shows how to:
- Create and configure the TrajectoryOptimizer
- Plan trajectories to configuration space targets
- Check for collisions before planning
- Execute optimized trajectories
- Configure optimization parameters
"""

# ============================================================================
# 1. Launch Simulation App
# ============================================================================
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import os

import cumotion

# Now we can import Isaac Sim modules
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import Articulation, GeomPrim
from isaacsim.core.experimental.utils.stage import add_reference_to_stage
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot_motion.cumotion import (
    CumotionWorldInterface,
    load_cumotion_supported_robot,
)

# temporary: TrajectoryOptimizer does not work on Windows.
if os.name != "nt":
    from isaacsim.robot_motion.cumotion import TrajectoryOptimizer

from isaacsim.robot_motion.cumotion.impl.utils import isaac_sim_to_cumotion_pose
from isaacsim.robot_motion.experimental.motion_generation import (
    ObstacleStrategy,
    SceneQuery,
    TrackableApi,
    WorldBinding,
)
from isaacsim.storage.native import get_assets_root_path


# ============================================================================
# 2. Setting Up the Optimizer
# ============================================================================
def setup_optimizer(world_binding):
    """Create and configure the TrajectoryOptimizer."""
    # Note: In this snippet, we assume the robot is already loaded in the stage
    # For the standalone example, the robot is loaded in main() before calling this function
    # Load robot configuration for supported robots
    cumotion_robot = load_cumotion_supported_robot("franka")
    articulation = Articulation("/panda")

    # <start-setup-optimizer-snippet>
    # Create trajectory optimizer
    # Use controlled_joint_names (not dof_names) to match cuMotion's expected joint space
    robot_joint_space = cumotion_robot.controlled_joint_names
    optimizer = TrajectoryOptimizer(
        cumotion_robot=cumotion_robot,
        robot_joint_space=robot_joint_space,
        cumotion_world_interface=world_binding.get_world_interface(),
    )
    # <end-setup-optimizer-snippet>

    return optimizer, cumotion_robot, articulation


# ============================================================================
# 3. Planning to Configuration Space Targets
# ============================================================================
def plan_to_cspace_target(optimizer, cumotion_robot, articulation, world_binding):
    """Plan a trajectory to a configuration space target."""
    # <start-update-world-state-snippet>
    # Update world state before planning
    world_binding.get_world_interface().update_world_to_robot_root_transforms(articulation.get_world_poses())
    world_binding.synchronize_transforms()
    # <end-update-world-state-snippet>

    # <start-plan-to-cspace-target-snippet>
    # Get initial and target configurations
    # Use default configuration as starting point (ensures valid configuration)
    q_initial = cumotion_robot.robot_description.default_cspace_configuration()
    q_initial[0] = -np.pi / 2
    q_initial[1] = -np.pi / 8

    # Create target configuration by modifying default
    q_target = cumotion_robot.robot_description.default_cspace_configuration()
    q_target[0] = np.pi / 2
    q_target[1] = -np.pi / 3

    # Create CSpaceTarget with target configuration
    # Path constraints must be explicitly set (even if to none())
    cspace_target = cumotion.TrajectoryOptimizer.CSpaceTarget(
        q_target,
        translation_path_constraint=cumotion.TrajectoryOptimizer.CSpaceTarget.TranslationPathConstraint.none(),
        orientation_path_constraint=cumotion.TrajectoryOptimizer.CSpaceTarget.OrientationPathConstraint.none(),
    )

    # Plan trajectory
    trajectory = optimizer.plan_to_goal(q_initial, cspace_target)

    if trajectory is None:
        print("Planning failed! Check warnings for failure status.")
        # Common issues:
        # - Start/goal configurations outside joint limits
        # - Start/goal configurations in collision
        # - Insufficient optimization parameters
    else:
        print(f"Planning succeeded! Trajectory duration: {trajectory.duration}")
    # <end-plan-to-cspace-target-snippet>

    return trajectory


# ============================================================================
# 4. Planning to Task-Space Targets
# ============================================================================
def plan_to_task_space_target(optimizer, cumotion_robot, articulation, world_binding, target_cube):
    """Plan a trajectory to a task-space target (from target cube position)."""
    # <start-update-world-state-snippet>
    # Update world state before planning
    world_binding.get_world_interface().update_world_to_robot_root_transforms(articulation.get_world_poses())
    world_binding.synchronize_transforms()
    # <end-update-world-state-snippet>

    # <start-plan-to-task-space-target-snippet>
    # Get target cube pose in world frame
    target_positions, target_orientations = target_cube.get_world_poses()
    target_position_world = target_positions.numpy()[0]
    target_orientation_world = target_orientations.numpy()[0]  # quaternion wxyz

    # Get robot base transform
    robot_base_positions, robot_base_orientations = articulation.get_world_poses()

    # Convert target pose from world frame to robot base frame
    target_pose_base = isaac_sim_to_cumotion_pose(
        position_world_to_target=target_position_world,
        orientation_world_to_target=target_orientation_world,
        position_world_to_base=robot_base_positions,
        orientation_world_to_base=robot_base_orientations,
    )

    # Create TaskSpaceTarget
    task_space_target = cumotion.TrajectoryOptimizer.TaskSpaceTarget(
        translation_constraint=cumotion.TrajectoryOptimizer.TranslationConstraint.target(target_pose_base.translation),
        orientation_constraint=cumotion.TrajectoryOptimizer.OrientationConstraint.terminal_target(
            target_pose_base.rotation
        ),
    )

    # Use default configuration as starting point (ensures valid configuration)
    q_initial = cumotion_robot.robot_description.default_cspace_configuration()
    q_initial[0] = -np.pi / 2
    q_initial[1] = -np.pi / 8

    # Plan trajectory
    trajectory = optimizer.plan_to_goal(q_initial, task_space_target)

    if trajectory is None:
        print("Planning failed! Check warnings for failure status.")
        # Common issues:
        # - Start configuration outside joint limits or in collision
        # - Target pose unreachable
        # - Insufficient optimization parameters
    else:
        print(f"Planning succeeded! Trajectory duration: {trajectory.duration}")
    # <end-plan-to-task-space-target-snippet>

    return trajectory


# ============================================================================
# 5. Optional: Checking for Collisions
# ============================================================================
def check_for_collisions(cumotion_robot, world_binding, q_initial, q_target):
    """Check if initial or target configurations are in collision."""
    # <start-check-collisions-snippet>
    # Create robot-world inspector for collision checking
    robot_world_inspector = cumotion.create_robot_world_inspector(
        cumotion_robot.robot_description,
        world_binding.get_world_interface().world_view,
    )

    # Ensure world view is up to date before collision checks
    world_binding.get_world_interface().world_view.update()

    if robot_world_inspector.in_self_collision(q_initial) or robot_world_inspector.in_collision_with_obstacle(
        q_initial
    ):
        print("Initial configuration is in collision!")
        return False

    if robot_world_inspector.in_self_collision(q_target) or robot_world_inspector.in_collision_with_obstacle(q_target):
        print("Target configuration is in collision!")
        return False

    return True
    # <end-check-collisions-snippet>


# ============================================================================
# 6. Executing Trajectories
# ============================================================================
def execute_trajectory(trajectory, articulation, trajectory_time, step):
    """Execute a trajectory in an update loop."""
    if trajectory is None:
        return trajectory_time

    # Sample trajectory at current time
    target_state = trajectory.get_target_state(trajectory_time)

    if target_state is not None and target_state.joints.positions is not None:
        articulation.set_dof_position_targets(
            positions=target_state.joints.positions,
            dof_indices=target_state.joints.position_indices,
        )

    # Advance trajectory time
    trajectory_time += step

    # Clamp to trajectory duration
    if trajectory_time >= trajectory.duration:
        trajectory_time = trajectory.duration

    return trajectory_time


# ============================================================================
# 7. Accessing cuMotion Parameters
# ============================================================================
def access_parameters(optimizer):
    """Demonstrate accessing and modifying cuMotion parameters."""
    # <start-access-parameters-snippet>
    # Get the underlying cuMotion config
    config = optimizer.get_trajectory_optimizer_config()

    # Modify parameters using set_param
    config.set_param(
        "enable_self_collision",
        cumotion.TrajectoryOptimizerConfig.ParamValue(False),
    )
    # <end-access-parameters-snippet>


# ============================================================================
# 8. Main Example
# ============================================================================
def main():
    """Run the complete example."""

    if os.name == "nt":
        print("Trajectory optimizer is not available on Windows.")
        return

    # Setup scene
    stage_utils.create_new_stage(template="sunlight")
    stage_utils.set_stage_units(meters_per_unit=1.0)

    # Load robot
    robot_prim_path = "/panda"
    path_to_robot_usd = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
    add_reference_to_stage(path_to_robot_usd, robot_prim_path)
    articulation = Articulation(robot_prim_path)

    # Create target cube (non-collision, can be moved around)
    angle = np.pi / 2
    target_orientation = np.array([np.cos(angle / 2), 0.0, np.sin(angle / 2), 0.0])
    target_cube = Cube(paths="/World/target", sizes=0.04, positions=[0.5, 0.0, 0.7], orientations=target_orientation)

    # Create obstacle
    obstacle_path = "/World/obstacle"
    Cube(obstacle_path, sizes=0.1, positions=[0.25, 0.0, 0.5])
    GeomPrim(obstacle_path, apply_collision_apis=True)

    # Create world binding
    scene_query = SceneQuery()
    robot_base_positions, robot_base_orientations = articulation.get_world_poses()
    search_origin = robot_base_positions.numpy()[0] if robot_base_positions.shape[0] > 0 else [0.0, 0.0, 0.0]
    objects = scene_query.get_prims_in_aabb(
        search_box_origin=search_origin,
        search_box_minimum=[-10.0, -10.0, -10.0],
        search_box_maximum=[10.0, 10.0, 10.0],
        tracked_api=TrackableApi.PHYSICS_COLLISION,
        exclude_prim_paths=[robot_prim_path, "/World/target"],  # Exclude robot and target cube
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

    # Setup optimizer
    optimizer, cumotion_robot, articulation = setup_optimizer(world_binding)

    # Test parameter access
    access_parameters(optimizer)

    # Get configurations for planning
    q_initial = cumotion_robot.robot_description.default_cspace_configuration()
    q_initial[0] = -np.pi / 2
    q_initial[1] = -np.pi / 8
    q_target = cumotion_robot.robot_description.default_cspace_configuration()
    q_target[0] = np.pi / 2
    q_target[1] = -np.pi / 3

    # Check for collisions
    check_for_collisions(cumotion_robot, world_binding, q_initial, q_target)

    # Plan to C-space target
    trajectory = plan_to_cspace_target(optimizer, cumotion_robot, articulation, world_binding)

    # Plan to task-space target (using target cube)
    trajectory2 = plan_to_task_space_target(optimizer, cumotion_robot, articulation, world_binding, target_cube)

    print("Trajectory optimizer example complete!")


if __name__ == "__main__":
    main()
    simulation_app.close()
