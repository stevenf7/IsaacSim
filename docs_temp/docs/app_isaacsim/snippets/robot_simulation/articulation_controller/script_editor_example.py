import asyncio

import numpy as np
from isaacsim.core.api.world import World
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import get_assets_root_path


async def robot_control_example():
    if World.instance():
        World.instance().clear_instance()
    world = World()
    await world.initialize_simulation_context_async()
    world.scene.add_default_ground_plane()

    # Load the robot USD file
    usd_path = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
    prim_path = "/World/envs/env_0/panda"
    add_reference_to_stage(usd_path, prim_path)

    # Create SingleArticulation wrapper (automatically creates articulation controller)
    robot = SingleArticulation(prim_path=prim_path, name="franka_panda")
    await world.reset_async()

    # Initialize the robot (initializes articulation controller internally)
    robot.initialize()

    # Run simulation
    await world.play_async()

    # Get current joint positions
    current_positions = robot.get_joint_positions()
    print(f"Current joint positions: {current_positions}")

    # Create target positions
    target_positions = np.array([0.0, -1.5, 0.0, -2.8, 0.0, 2.8, 1.2, 0.04, 0.04])

    # Create and apply articulation action
    action = ArticulationAction(joint_positions=target_positions)
    robot.apply_action(action)

    await asyncio.sleep(5.0)  # Run for 5 seconds to reach target positions

    # Get current joint positions
    current_positions = robot.get_joint_positions()
    print(f"Current joint positions: {current_positions}")

    world.pause()


# Run the example
asyncio.ensure_future(robot_control_example())
