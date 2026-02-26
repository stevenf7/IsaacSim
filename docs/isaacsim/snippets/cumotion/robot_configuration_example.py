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

This file contains code snippets that are displayed in the cuMotion Robot
Configuration tutorial documentation. If you modify this file, you MUST also
update the corresponding tutorial extension at:
    source/extensions/isaacsim.robot_motion.cumotion.examples/isaacsim/robot_motion/cumotion/examples/robot_configuration/

The tutorial RST file is at:
    docs/isaacsim/cumotion/tutorial_robot_configuration.rst

================================================================================
"""

"""
Complete example demonstrating robot configuration loading.

This example shows how to:
- Load supported robot configurations
- Load custom robot configurations from URDF/XRDF files
- Access robot description and kinematics
- Use robot configurations with cuMotion components
"""

# ============================================================================
# 1. Launch Simulation App
# ============================================================================
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

# Now we can import Isaac Sim modules
import pathlib

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.robot_motion.cumotion as cu_mg
from isaacsim.robot_motion.cumotion import (
    CumotionWorldInterface,
    GraphBasedMotionPlanner,
    RmpFlowController,
    load_cumotion_robot,
    load_cumotion_supported_robot,
)


# ============================================================================
# 1. Loading Supported Robots
# ============================================================================
def load_supported_robot():
    """Load a pre-configured robot from the extension."""
    # <start-load-supported-robot-snippet>
    import isaacsim.robot_motion.cumotion as cu_mg

    # Load a supported robot
    robot = cu_mg.load_cumotion_supported_robot("franka")
    # <end-load-supported-robot-snippet>

    return robot


# ============================================================================
# 2. Loading Custom Robot Configurations
# ============================================================================
def load_custom_robot_default_names():
    """Load a custom robot with default filenames."""

    import pathlib

    import isaacsim.core.experimental.utils.app as app_utils

    # Get the extension directory and specify the robot configuration directory
    ext_directory = pathlib.Path(app_utils.get_extension_path("isaacsim.robot_motion.cumotion"))
    robot_directory = ext_directory / "robot_configurations" / "franka"

    # <start-load-custom-robot-default-snippet>
    import isaacsim.robot_motion.cumotion as cu_mg

    # Generate configuration with default filenames (robot.urdf, robot.xrdf)
    robot = cu_mg.load_cumotion_robot(directory=robot_directory)
    # <end-load-custom-robot-default-snippet>

    return robot


def load_custom_robot_custom_names():
    """Load a custom robot with custom filenames."""
    import pathlib

    import isaacsim.core.experimental.utils.app as app_utils

    ext_directory = pathlib.Path(app_utils.get_extension_path("isaacsim.robot_motion.cumotion"))
    absolute_path_to_robot_directory = ext_directory / "robot_configurations" / "franka"

    # <start-load-custom-robot-custom-snippet>
    import isaacsim.robot_motion.cumotion as cu_mg

    robot = cu_mg.load_cumotion_robot(
        directory=absolute_path_to_robot_directory,
        urdf_filename="robot.urdf",  # if your URDF has a different name, use it.
        xrdf_filename="robot.xrdf",  # if your XRDF has a different name, use it.
    )
    # <end-load-custom-robot-custom-snippet>

    return robot


# ============================================================================
# 3. Accessing Robot Description and Kinematics
# ============================================================================
def access_robot_description():
    """Access robot description and kinematics."""
    # <start-access-robot-description-snippet>
    robot = load_cumotion_supported_robot("franka")

    # Access the robot description
    robot_description = robot.robot_description

    # Get tool frame names
    tool_frames = robot_description.tool_frame_names()

    # Get number of configuration space coordinates
    num_dofs = robot_description.num_cspace_coords()

    # Access the kinematics solver
    # (See cuMotion documentation for kinematics API)
    kinematics = robot.kinematics
    # <end-access-robot-description-snippet>

    return robot, robot_description, tool_frames, num_dofs, kinematics


def access_controlled_joints():
    """Access controlled joint names."""
    # <start-access-controlled-joints-snippet>
    robot = load_cumotion_supported_robot("franka")

    # Controlled joints match the configuration space coordinates
    controlled_joints = robot.controlled_joint_names

    # This is equivalent to:
    controlled_joints = [
        robot.robot_description.cspace_coord_name(i) for i in range(robot.robot_description.num_cspace_coords())
    ]
    # <end-access-controlled-joints-snippet>

    return controlled_joints


# ============================================================================
# 4. Loading Configuration Files with RMPflow
# ============================================================================
def load_rmpflow_config_relative(world_interface, robot_joint_space, robot_site_space):
    """Load RMPflow configuration using relative path."""
    # <start-load-rmpflow-relative-snippet>
    robot = load_cumotion_supported_robot("franka")

    # The RmpFlowController automatically resolves relative paths relative to robot.directory
    controller = RmpFlowController(
        cumotion_robot=robot,
        cumotion_world_interface=world_interface,
        robot_joint_space=robot_joint_space,
        robot_site_space=robot_site_space,
        rmp_flow_configuration_filename="rmp_flow.yaml",  # Relative to robot.directory
    )
    # <end-load-rmpflow-relative-snippet>

    return controller


def load_rmpflow_config_absolute(world_interface, robot_joint_space, robot_site_space):
    """Load RMPflow configuration using absolute path."""
    # Get extension path for absolute path example
    ext_directory = pathlib.Path(app_utils.get_extension_path("isaacsim.robot_motion.cumotion"))
    absolute_path_to_config = str(ext_directory / "robot_configurations" / "franka" / "rmp_flow.yaml")

    # <start-load-rmpflow-absolute-snippet>
    robot = load_cumotion_supported_robot("franka")

    # Or specify an absolute path
    controller = RmpFlowController(
        cumotion_robot=robot,
        cumotion_world_interface=world_interface,
        robot_joint_space=robot_joint_space,
        robot_site_space=robot_site_space,
        rmp_flow_configuration_filename=absolute_path_to_config,
    )
    # <end-load-rmpflow-absolute-snippet>

    return controller


# ============================================================================
# 5. Loading Configuration Files with Graph Planner
# ============================================================================
def load_graph_planner_config_relative(world_interface):
    """Load graph planner configuration using relative path."""
    # <start-load-graph-planner-relative-snippet>
    robot = load_cumotion_supported_robot("franka")

    # Relative paths are automatically resolved relative to robot.directory
    planner = GraphBasedMotionPlanner(
        cumotion_robot=robot,
        cumotion_world_interface=world_interface,
        graph_planner_config_filename="graph_based_motion_planner_config.yaml",
    )
    # <end-load-graph-planner-relative-snippet>

    return planner


def load_graph_planner_config_absolute(world_interface):
    """Load graph planner configuration using absolute path."""
    # Get extension path for absolute path example
    ext_directory = pathlib.Path(app_utils.get_extension_path("isaacsim.robot_motion.cumotion"))
    absolute_path_to_config = str(
        ext_directory / "robot_configurations" / "franka" / "graph_based_motion_planner_config.yaml"
    )

    # <start-load-graph-planner-absolute-snippet>
    robot = load_cumotion_supported_robot("franka")

    # Or specify an absolute path
    planner = GraphBasedMotionPlanner(
        cumotion_robot=robot,
        cumotion_world_interface=world_interface,
        graph_planner_config_filename=absolute_path_to_config,
    )
    # <end-load-graph-planner-absolute-snippet>

    return planner


# ============================================================================
# Main function to run all examples
# ============================================================================
def main():
    """Run all robot configuration examples."""
    # Load supported robot
    robot = load_supported_robot()

    # Load custom robot configurations
    robot_default = load_custom_robot_default_names()
    robot_custom = load_custom_robot_custom_names()

    # Access robot description
    robot, robot_description, tool_frames, num_dofs, kinematics = access_robot_description()

    # Access controlled joints
    controlled_joints = access_controlled_joints()

    # Test loading configuration files with RMPflow
    # Create minimal world interface for testing
    world_interface = CumotionWorldInterface()
    robot_joint_space = robot.controlled_joint_names
    robot_site_space = robot.robot_description.tool_frame_names()

    # Load RMPflow configurations
    controller_relative = load_rmpflow_config_relative(world_interface, robot_joint_space, robot_site_space)
    controller_absolute = load_rmpflow_config_absolute(world_interface, robot_joint_space, robot_site_space)
    planner_relative = load_graph_planner_config_relative(world_interface)
    planner_absolute = load_graph_planner_config_absolute(world_interface)

    print("Robot configuration example complete!")


if __name__ == "__main__":
    main()
