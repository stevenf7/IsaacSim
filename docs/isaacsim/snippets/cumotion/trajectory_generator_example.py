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

This file contains code snippets that are displayed in the cuMotion Trajectory Generator
tutorial documentation. If you modify this file, you MUST also update the
corresponding tutorial extension at:
    source/extensions/isaacsim.robot_motion.cumotion.examples/isaacsim/robot_motion/cumotion/examples/trajectory_generator/

The tutorial RST file is at:
    docs/isaacsim/cumotion/tutorial_trajectory_generator.rst

================================================================================
"""

"""
Complete example demonstrating TrajectoryGenerator usage.

This example shows how to:
- Generate trajectories from C-space waypoints
- Create and use path specifications
- Convert between world coordinates and robot base frame coordinates
- Execute trajectories using the Trajectory interface
- Configure trajectory parameters
"""

# ============================================================================
# 1. Launch Simulation App
# ============================================================================
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import cumotion
import numpy as np

# Now we can import Isaac Sim modules
import omni.timeline
import warp as wp
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot_motion.cumotion import (
    TrajectoryGenerator,
    load_cumotion_supported_robot,
)
from isaacsim.robot_motion.cumotion.impl.utils import isaac_sim_to_cumotion_pose


# ============================================================================
# 2. Generating from C-Space Waypoints
# ============================================================================
def generate_from_cspace_waypoints():
    """Generate trajectories directly from C-space waypoints."""
    import isaacsim.core.experimental.utils.stage as stage_utils
    from isaacsim.core.experimental.utils.stage import add_reference_to_stage
    from isaacsim.storage.native import get_assets_root_path

    # Setup stage and load robot
    stage_utils.create_new_stage(template="default stage")
    stage_utils.set_stage_units(meters_per_unit=1.0)
    robot_prim_path = "/ur10"
    try:
        path_to_robot_usd = get_assets_root_path() + "/Isaac/Robots/UniversalRobots/ur10/ur10.usd"
        add_reference_to_stage(path_to_robot_usd, robot_prim_path)
    except RuntimeError as e:
        print(f"Warning: Could not load robot from assets: {e}")
        print("This example requires a connection to Omniverse Nucleus or local assets.")
        print("Please ensure you have access to Isaac Sim assets.")
        raise

    # <start-initialize-generator-snippet>
    # Load robot configuration
    cumotion_robot = load_cumotion_supported_robot("ur10")
    articulation = Articulation(robot_prim_path)

    # Create trajectory generator
    generator = TrajectoryGenerator(
        cumotion_robot=cumotion_robot,
        robot_joint_space=articulation.dof_names,
    )
    # <end-initialize-generator-snippet>

    # <start-generate-from-cspace-waypoints-snippet>
    # Define waypoints
    waypoints = [
        np.array([-0.41, 0.5, -2.36, -1.28, 5.13, -4.71]),
        np.array([-1.43, 1.0, -2.58, -1.53, 6.0, -4.74]),
        np.array([-2.83, 0.34, -2.11, -1.38, 1.26, -4.71]),
    ]

    # Generate trajectory
    trajectory = generator.generate_trajectory_from_cspace_waypoints(waypoints)

    if trajectory is None:
        print("Failed to generate trajectory")
    else:
        print(f"Trajectory duration: {trajectory.duration} seconds")
    # <end-generate-from-cspace-waypoints-snippet>

    return trajectory, generator, articulation


# ============================================================================
# 3. Generating from Path Specifications
# ============================================================================
def generate_from_path_specification(generator):
    """Generate trajectories from cuMotion path specifications."""
    # <start-generate-from-path-spec-snippet>
    # Create C-space path spec
    initial_position = np.array([-0.41, 0.5, -2.36, -1.28, 5.13, -4.71])
    path_spec = cumotion.create_cspace_path_spec(initial_position)
    path_spec.add_cspace_waypoint(np.array([-1.43, 1.0, -2.58, -1.53, 6.0, -4.74]))
    path_spec.add_cspace_waypoint(np.array([-2.83, 0.34, -2.11, -1.38, 1.26, -4.71]))

    # Convert C-space path spec to linear path before generating trajectory
    linear_path = cumotion.create_linear_cspace_path(path_spec)

    # Generate trajectory from linear path
    trajectory = generator.generate_trajectory_from_path_specification(linear_path)
    # <end-generate-from-path-spec-snippet>

    return trajectory


# ============================================================================
# 4. Task-Space Path Specifications
# ============================================================================
def generate_from_task_space_path_spec(generator, articulation):
    """Generate trajectories from task-space path specifications."""
    # <start-task-space-path-spec-snippet>
    # Get robot base transform directly from articulation
    robot_base_positions, robot_base_orientations = articulation.get_world_poses()

    # Create task-space path spec
    task_space_position_targets = np.array(
        [[0.3, -0.3, 0.1], [0.3, 0.3, 0.1], [0.3, 0.3, 0.5], [0.3, -0.3, 0.5], [0.3, -0.3, 0.1]]
    )
    task_space_orientation_targets = np.tile(np.array([0, 1, 0, 0]), (5, 1))  # quaternion wxyz

    initial_pose = isaac_sim_to_cumotion_pose(
        position_world_to_target=task_space_position_targets[0],
        orientation_world_to_target=task_space_orientation_targets[0],
        position_world_to_base=robot_base_positions,
        orientation_world_to_base=robot_base_orientations,
    )
    path_spec = cumotion.create_task_space_path_spec(initial_pose)

    # Add linear path segments for remaining waypoints
    for i in range(1, len(task_space_position_targets)):
        target_pose = isaac_sim_to_cumotion_pose(
            position_world_to_target=task_space_position_targets[i],
            orientation_world_to_target=task_space_orientation_targets[i],
            position_world_to_base=robot_base_positions,
            orientation_world_to_base=robot_base_orientations,
        )
        path_spec.add_linear_path(target_pose)

    # Generate trajectory (automatically converts to C-space)
    trajectory = generator.generate_trajectory_from_path_specification(
        path_spec,
        tool_frame_name="ee_link",
    )
    # <end-task-space-path-spec-snippet>

    return trajectory


# ============================================================================
# 5. Executing Trajectories
# ============================================================================
def execute_trajectory(trajectory, articulation, t):
    """Execute a trajectory at time t."""
    # Get trajectory state at time t
    target_state = trajectory.get_target_state(t)

    if target_state is not None and target_state.joints.positions is not None:
        # Apply to robot
        articulation.set_dof_position_targets(
            positions=target_state.joints.positions,
            dof_indices=target_state.joints.position_indices,
        )

    # Check if trajectory is complete
    if t >= trajectory.duration:
        print("Trajectory complete")


# ============================================================================
# 6. Configuring Trajectory Parameters
# ============================================================================
def configure_trajectory_parameters(generator):
    """Access and modify trajectory generator parameters."""
    # <start-configure-trajectory-parameters-snippet>
    # Get the underlying cuMotion generator
    cspace_gen = generator.get_cspace_trajectory_generator()

    # Modify parameters using the cuMotion Python API
    # See the cuMotion Python API documentation for available parameters and methods
    # <end-configure-trajectory-parameters-snippet>


# ============================================================================
# 7. Main Example
# ============================================================================
def main():
    """Run the complete example."""

    # Generate from C-space waypoints
    trajectory, generator, articulation = generate_from_cspace_waypoints()

    # Test path specification generation
    if trajectory is not None:
        trajectory2 = generate_from_path_specification(generator)
        trajectory3 = generate_from_task_space_path_spec(generator, articulation)

    # Configure parameters
    configure_trajectory_parameters(generator)

    # Execute trajectory for a few steps
    if trajectory is not None:
        SimulationManager.set_physics_dt(1.0 / 60.0)
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        simulation_app.update()

        # Execute trajectory for a limited number of steps
        trajectory_time = 0.0
        step = 1.0 / 60.0
        max_steps = min(10, int(trajectory.duration / step) + 1)  # Run for 10 steps or until trajectory ends

        for _ in range(max_steps):
            simulation_app.update()
            execute_trajectory(trajectory, articulation, trajectory_time)
            trajectory_time += step
            if trajectory_time >= trajectory.duration:
                break

        timeline.pause()

    print("Trajectory generator example complete!")


if __name__ == "__main__":
    main()
    simulation_app.close()
