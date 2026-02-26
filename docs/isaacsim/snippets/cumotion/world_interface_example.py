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

This file contains code snippets that are displayed in the cuMotion World Interface
tutorial documentation. If you modify this file, you MUST also update the
corresponding tutorial extension at:
    source/extensions/isaacsim.robot_motion.cumotion.examples/isaacsim/robot_motion/cumotion/examples/world_interface/

The tutorial RST file is at:
    docs/isaacsim/cumotion/tutorial_world_interface.rst

================================================================================
"""

"""
Complete example demonstrating CumotionWorldInterface usage.

This example shows how to:
- Use SceneQuery to discover obstacles
- Configure ObstacleStrategy for different geometry types
- Create CumotionWorldInterface with WorldBinding
- Synchronize world state with different update styles
- Update robot base transforms
"""

# ============================================================================
# 1. Launch Simulation App
# ============================================================================
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np

# Now we can import Isaac Sim modules
import omni.timeline
from isaacsim.core.experimental.objects import Cone, Cube, Cylinder, Mesh
from isaacsim.core.experimental.prims import Articulation, GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.robot_motion.cumotion import CumotionWorldInterface
from isaacsim.robot_motion.experimental.motion_generation import (
    ObstacleConfiguration,
    ObstacleRepresentation,
    ObstacleStrategy,
    SceneQuery,
    TrackableApi,
    WorldBinding,
)


# ============================================================================
# 2. Scene Setup
# ============================================================================
def setup_scene():
    """Create a simple example scene with obstacles."""
    # Create a new stage from default template
    stage_utils.create_new_stage(template="default stage")
    stage_utils.set_stage_units(meters_per_unit=1.0)

    # Create a cube obstacle
    obstacle_path = "/World/obstacle"
    cube = Cube(obstacle_path, sizes=0.1, positions=[0.4, 0.0, 0.65])

    # Apply collision APIs
    GeomPrim(obstacle_path, apply_collision_apis=True)
    RigidPrim(obstacle_path, masses=[1.0])

    return cube


# ============================================================================
# 3. Searching for Obstacles
# ============================================================================
def search_for_obstacles():
    """Demonstrate SceneQuery usage."""
    # <start-search-obstacles-snippet>
    # Create scene query to discover obstacles
    scene_query = SceneQuery()

    # Find all objects in a bounding box
    objects = scene_query.get_prims_in_aabb(
        search_box_origin=[0.0, 0.0, 0.0],
        search_box_minimum=[-100.0, -100.0, -100.0],
        search_box_maximum=[100.0, 100.0, 100.0],
        tracked_api=TrackableApi.PHYSICS_COLLISION,
    )

    print("Discovered objects:", objects)
    # <end-search-obstacles-snippet>

    return objects


# ============================================================================
# 4. Configuring Obstacle Representations
# ============================================================================
def configure_obstacle_strategy():
    """Demonstrate ObstacleStrategy configuration."""
    # <start-configure-obstacle-strategy-snippet>
    # Set up obstacle strategy
    obstacle_strategy = ObstacleStrategy()

    # Set default safety tolerance for all obstacles
    obstacle_strategy.set_default_safety_tolerance(0.06)

    # Configure specific geometry types
    obstacle_strategy.set_default_configuration(
        Mesh,
        ObstacleConfiguration(
            representation=ObstacleRepresentation.OBB,  # Oriented Bounding Box
            safety_tolerance=0.01,
        ),
    )

    obstacle_strategy.set_default_configuration(
        Cone,
        ObstacleConfiguration(
            representation=ObstacleRepresentation.OBB,
            safety_tolerance=0.01,
        ),
    )

    obstacle_strategy.set_default_configuration(
        Cylinder,
        ObstacleConfiguration(
            representation=ObstacleRepresentation.OBB,
            safety_tolerance=0.01,
        ),
    )
    # <end-configure-obstacle-strategy-snippet>

    return obstacle_strategy


# ============================================================================
# 5. Creating the World Interface and World Binding
# ============================================================================
def create_world_binding(objects, obstacle_strategy):
    """Create CumotionWorldInterface and WorldBinding."""
    # <start-create-world-binding-snippet>
    # Create world interface with optional debug visualizations
    world_interface = CumotionWorldInterface(visualize_debug_prims=True)

    # Create world binding
    world_binding = WorldBinding(
        world_interface=world_interface,
        obstacle_strategy=obstacle_strategy,
        tracked_prims=objects,
        tracked_collision_api=TrackableApi.PHYSICS_COLLISION,
    )

    # Initialize the world binding (populates obstacles into cuMotion)
    world_binding.initialize()
    # <end-create-world-binding-snippet>

    return world_binding


# ============================================================================
# 6. Synchronizing the World Binding
# ============================================================================
def synchronize_transforms(world_binding):
    """Update only transforms (fastest, for static obstacles with moving robot base)."""
    # <start-synchronize-transforms-snippet>
    # Update only transforms (fastest, for static obstacles with moving robot base)
    world_binding.synchronize_transforms()
    # <end-synchronize-transforms-snippet>


def synchronize_properties(world_binding):
    """Update only properties (for obstacles that change size/shape or collision enabled state)."""
    # <start-synchronize-properties-snippet>
    # Update only properties (for obstacles that change size/shape or collision enabled state)
    # Note: cuMotion does not support updating the properties of obstacles.
    # The only property which supports updating in cuMotion is the collision enabled state.
    world_binding.synchronize_properties()
    # <end-synchronize-properties-snippet>


def synchronize_both(world_binding):
    """Update both transforms and properties."""
    # <start-synchronize-both-snippet>
    # Update both transforms and properties (most complete, but not recommended for high-frequency updates)
    world_binding.synchronize()
    # <end-synchronize-both-snippet>


# ============================================================================
# 7. Updating Robot Base Transforms
# ============================================================================
def update_robot_base_transforms(world_binding, articulation):
    """Update world interface with robot base transform."""
    # <start-update-robot-base-transforms-snippet>
    # Update world interface with robot base transform
    world_binding.get_world_interface().update_world_to_robot_root_transforms(articulation.get_world_poses())
    # <end-update-robot-base-transforms-snippet>


# ============================================================================
# 8. Main Example
# ============================================================================
def main():
    """Run the complete example."""
    from isaacsim.core.experimental.utils.stage import add_reference_to_stage
    from isaacsim.storage.native import get_assets_root_path

    # Setup scene
    setup_scene()

    # Search for obstacles
    objects = search_for_obstacles()

    # Configure obstacle strategy
    obstacle_strategy = configure_obstacle_strategy()

    # Create world binding
    world_binding = create_world_binding(objects, obstacle_strategy)

    # Test all synchronization methods
    synchronize_transforms(world_binding)
    synchronize_properties(world_binding)
    synchronize_both(world_binding)

    # Example: Load robot and update robot base transforms
    try:
        robot_prim_path = "/panda"
        path_to_robot_usd = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        add_reference_to_stage(path_to_robot_usd, robot_prim_path)
        articulation = Articulation(robot_prim_path)
        update_robot_base_transforms(world_binding, articulation)
    except Exception as e:
        print(f"Note: Could not load robot for base transform example: {e}")

    print("World interface example complete!")


if __name__ == "__main__":
    main()
    simulation_app.close()
