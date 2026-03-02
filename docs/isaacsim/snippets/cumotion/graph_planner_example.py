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

This file contains code snippets that are displayed in the cuMotion Graph-Based Motion Planner
tutorial documentation. If you modify this file, you MUST also update the
corresponding tutorial extension at:
    source/extensions/isaacsim.robot_motion.cumotion.examples/isaacsim/robot_motion/cumotion/examples/graph_planner/

The tutorial RST file is at:
    docs/isaacsim/cumotion/tutorial_graph_planner.rst

================================================================================
"""

"""
Complete example demonstrating GraphBasedMotionPlanner usage.

This example shows how to:
- Set up the graph-based motion planner with world state management
- Plan to C-space, task-space, and translation-only targets
- Execute planned paths using trajectories
- Update world state for accurate planning
- Configure planner parameters
"""

# ============================================================================
# 1. Launch Simulation App
# ============================================================================
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import numpy as np

# Now we can import Isaac Sim modules
import omni.timeline
import warp as wp
from isaacsim.core.experimental.objects import Cone, Cube, Cylinder, Mesh
from isaacsim.core.experimental.prims import Articulation, GeomPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot_motion.cumotion import (
    CumotionWorldInterface,
    GraphBasedMotionPlanner,
    load_cumotion_supported_robot,
)
from isaacsim.robot_motion.experimental.motion_generation import (
    JointState,
    ObstacleConfiguration,
    ObstacleRepresentation,
    ObstacleStrategy,
    RobotState,
    SceneQuery,
    TrackableApi,
    TrajectoryFollower,
    WorldBinding,
)


# ============================================================================
# 2. Setting Up the Planner
# ============================================================================
def setup_planner():
    """Create and configure the GraphBasedMotionPlanner with world state management."""
    import isaacsim.core.experimental.utils.stage as stage_utils
    from isaacsim.core.experimental.utils.stage import add_reference_to_stage
    from isaacsim.storage.native import get_assets_root_path

    # Setup stage
    stage_utils.create_new_stage(template="default stage")
    stage_utils.set_stage_units(meters_per_unit=1.0)

    # Load robot
    robot_prim_path = "/panda"
    path_to_robot_usd = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
    add_reference_to_stage(path_to_robot_usd, robot_prim_path)

    # Load robot configuration
    cumotion_robot = load_cumotion_supported_robot("franka")
    articulation = Articulation(robot_prim_path)

    # Create obstacle
    obstacle_path = "/World/obstacle"
    obstacle_size = 0.1
    obstacle_position = np.array([0.25, 0.0, 0.5])

    cube = Cube(obstacle_path, sizes=obstacle_size, positions=[obstacle_position])
    GeomPrim(obstacle_path, apply_collision_apis=True)

    # Create scene query to discover obstacles
    scene_query = SceneQuery()

    # Get robot base transform
    robot_base_positions, robot_base_orientations = articulation.get_world_poses()

    # Get all objects surrounding the robot
    search_origin = robot_base_positions.numpy()[0] if robot_base_positions.shape[0] > 0 else [0.0, 0.0, 0.0]
    objects = scene_query.get_prims_in_aabb(
        search_box_origin=search_origin,
        search_box_minimum=[-10.0, -10.0, -10.0],
        search_box_maximum=[10.0, 10.0, 10.0],
        tracked_api=TrackableApi.PHYSICS_COLLISION,
        exclude_prim_paths=[robot_prim_path],  # don't include the robot itself
    )

    # Set up obstacle strategy
    obstacle_strategy = ObstacleStrategy()
    obstacle_strategy.set_default_configuration(Mesh, ObstacleConfiguration("obb", 0.01))
    obstacle_strategy.set_default_configuration(Cone, ObstacleConfiguration("obb", 0.01))
    obstacle_strategy.set_default_configuration(Cylinder, ObstacleConfiguration("obb", 0.01))

    # Create world binding
    world_binding = WorldBinding(
        world_interface=CumotionWorldInterface(),
        obstacle_strategy=obstacle_strategy,
        tracked_prims=objects,
        tracked_collision_api=TrackableApi.PHYSICS_COLLISION,
    )

    # Populate the world
    world_binding.initialize()

    # Update world interface with robot base transform
    world_binding.get_world_interface().update_world_to_robot_root_transforms(
        poses=(robot_base_positions, robot_base_orientations)
    )

    # Synchronize transforms before planning
    world_binding.synchronize_transforms()

    # <start-setup-planner-snippet>
    # Create graph-based motion planner
    planner = GraphBasedMotionPlanner(
        cumotion_robot=cumotion_robot,
        cumotion_world_interface=world_binding.get_world_interface(),
    )
    # <end-setup-planner-snippet>

    return planner, cumotion_robot, articulation, world_binding


# ============================================================================
# 3. Planning to C-Space Targets
# ============================================================================
def plan_to_cspace_target(planner):
    """Plan to a configuration space (joint space) position."""
    # <start-plan-to-cspace-target-snippet>
    # Define initial and target joint configurations
    q_initial = np.array([0.0, -0.5, 0.0, -2.0, 0.0, 1.5, 0.75])
    q_target = np.array([0.5, -0.3, 0.5, -1.5, 0.5, 1.2, 0.5])

    # Plan path
    path = planner.plan_to_cspace_target(q_initial, q_target)

    if path is None:
        print("Planning failed!")
    else:
        print(f"Path found with {path.get_waypoints_count()} waypoints")
    # <end-plan-to-cspace-target-snippet>

    return path


# ============================================================================
# 4. Planning to Task-Space Targets
# ============================================================================
def plan_to_pose_target(planner):
    """Plan to a task-space pose target."""
    # <start-plan-to-pose-target-snippet>
    # Define target pose in world frame
    target_position_world = np.array([0.6, 0.1, 0.5])
    target_orientation_world = np.array([1.0, 0.0, 0.0, 0.0])  # quaternion wxyz

    # Plan to task-space target (takes world-frame coordinates)
    q_initial = np.array([0.0, -0.5, 0.0, -2.0, 0.0, 1.5, 0.75])
    path = planner.plan_to_pose_target(q_initial, target_position_world, target_orientation_world)
    # <end-plan-to-pose-target-snippet>

    return path


# ============================================================================
# 5. Planning to Translation-Only Targets
# ============================================================================
def plan_to_translation_target(planner):
    """Plan to a translation-only target (position only, not orientation)."""
    # <start-plan-to-translation-target-snippet>
    # Define target position in world frame
    target_position_world = np.array([0.6, 0.1, 0.5])

    # Plan to translation-only target (takes world-frame coordinates)
    q_initial = np.array([0.0, -0.5, 0.0, -2.0, 0.0, 1.5, 0.75])
    path = planner.plan_to_translation_target(q_initial, target_position_world)
    # <end-plan-to-translation-target-snippet>

    return path


# ============================================================================
# 6. Executing Planned Paths
# ============================================================================
def convert_path_to_trajectory(path, cumotion_robot, articulation):
    """Convert Path to minimal-time trajectory."""
    if path is None:
        return None

    robot_joint_space = articulation.dof_names
    controlled_joint_names = cumotion_robot.controlled_joint_names

    # <start-convert-path-to-trajectory-snippet>
    # Convert Path to minimal-time trajectory using Motion Generation API
    # Use reasonable velocity and acceleration limits (adjust based on robot capabilities)
    max_velocities = np.array([2.0, 2.0, 2.0, 2.0, 2.5, 2.5, 2.5])  # rad/s
    max_accelerations = np.array([2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0])  # rad/s²

    trajectory = path.to_minimal_time_joint_trajectory(
        max_velocities=max_velocities,
        max_accelerations=max_accelerations,
        robot_joint_space=robot_joint_space,
        active_joints=controlled_joint_names,
    )
    # <end-convert-path-to-trajectory-snippet>

    return trajectory


def execute_trajectory_directly(trajectory, articulation, t: float):
    """Execute trajectory by sampling and applying joint states directly."""
    if trajectory is None:
        return

    # <start-execute-trajectory-directly-snippet>
    # Sample the trajectory at the current time
    target_state = trajectory.get_target_state(t)
    if target_state is not None and target_state.joints.positions is not None:
        # Apply directly to the articulation
        articulation.set_dof_position_targets(
            positions=target_state.joints.positions,
            dof_indices=target_state.joints.position_indices,
        )
    # <end-execute-trajectory-directly-snippet>


def execute_trajectory_with_follower(
    trajectory, articulation, robot_joint_space, t: float, step: float, simulation_app
):
    """Execute trajectory using TrajectoryFollower for integration into control systems."""
    if trajectory is None:
        return None

    # <start-execute-trajectory-with-follower-snippet>
    # Create TrajectoryFollower controller
    follower = TrajectoryFollower()

    # Set the trajectory
    follower.set_trajectory(trajectory)

    # Get current estimated state
    joint_state = JointState.from_name(
        robot_joint_space=robot_joint_space,
        positions=(robot_joint_space, articulation.get_dof_positions()),
        velocities=(robot_joint_space, articulation.get_dof_velocities()),
    )
    estimated_state = RobotState(joints=joint_state)

    # Reset the follower (sets start time)
    follower.reset(estimated_state, None, t)

    # In your control loop, call forward to get desired state
    desired_state = follower.forward(estimated_state, None, t)
    while desired_state is not None:
        if desired_state.joints.positions is not None:
            # Apply desired state to robot
            articulation.set_dof_position_targets(
                positions=desired_state.joints.positions,
                dof_indices=desired_state.joints.position_indices,
            )
        # Update simulation
        simulation_app.update()
        # Update estimated state and time for next iteration
        estimated_state = RobotState(
            joints=JointState.from_name(
                robot_joint_space=robot_joint_space,
                positions=(robot_joint_space, articulation.get_dof_positions()),
                velocities=(robot_joint_space, articulation.get_dof_velocities()),
            )
        )
        t += step  # Advance time
        desired_state = follower.forward(estimated_state, None, t)
    # <end-execute-trajectory-with-follower-snippet>

    return follower


# ============================================================================
# 7. Updating World State
# ============================================================================
def update_world_state(world_binding, articulation):
    """Update world binding before planning if obstacles or robot base have moved."""
    # <start-update-world-state-snippet>
    # Update robot base transform
    world_binding.get_world_interface().update_world_to_robot_root_transforms(articulation.get_world_poses())

    # Synchronize transforms (updates all obstacles and world state)
    world_binding.synchronize_transforms()
    # <end-update-world-state-snippet>


# ============================================================================
# 8. Configuring Planner Parameters
# ============================================================================
def configure_planner_parameters(planner):
    """Access the underlying cuMotion planner configuration to modify parameters."""
    # <start-configure-planner-parameters-snippet>
    # Get the underlying cuMotion planner config
    planner_config = planner.get_graph_planner_config()

    # Modify parameters directly per cuMotion documentation
    # (See cuMotion API documentation for available parameters)
    # <end-configure-planner-parameters-snippet>


# ============================================================================
# 9. Main Example
# ============================================================================
def main():
    """Run the complete example."""

    # Setup planner
    planner, cumotion_robot, articulation, world_binding = setup_planner()

    # Test parameter configuration
    configure_planner_parameters(planner)

    # Update world state before planning
    update_world_state(world_binding, articulation)

    # Plan to C-space target
    path = plan_to_cspace_target(planner)

    # Convert path to trajectory and execute
    if path is not None:
        robot_joint_space = articulation.dof_names
        controlled_joint_names = cumotion_robot.controlled_joint_names

        # Convert path to trajectory
        trajectory = convert_path_to_trajectory(path, cumotion_robot, articulation)

        # Execute trajectory using different methods
        if trajectory is not None:
            SimulationManager.set_physics_dt(1.0 / 60.0)
            timeline = omni.timeline.get_timeline_interface()
            timeline.play()
            simulation_app.update()

            step = 1.0 / 60.0
            t = 0.0

            # Test direct execution
            print("Testing direct trajectory execution...")
            max_steps = min(5, int(trajectory.duration / step) + 1)
            for _ in range(max_steps):
                simulation_app.update()
                execute_trajectory_directly(trajectory, articulation, t)
                t += step
                if t >= trajectory.duration:
                    break

            # Reset time for follower test
            t = 0.0

            # Test TrajectoryFollower execution
            print("Testing TrajectoryFollower execution...")
            execute_trajectory_with_follower(trajectory, articulation, robot_joint_space, t, step, simulation_app)

            timeline.pause()

    # Test other planning methods (may fail, but code is tested)
    plan_to_pose_target(planner)
    plan_to_translation_target(planner)

    print("Graph planner example complete!")


if __name__ == "__main__":
    main()
    simulation_app.close()
