import asyncio

import numpy as np
from isaacsim.core.api import World
from isaacsim.robot.wheeled_robots.controllers.differential_controller import DifferentialController
from isaacsim.robot.wheeled_robots.robots import WheeledRobot
from isaacsim.storage.native import get_assets_root_path


async def differential_controller_example():
    if World.instance():
        World.instance().clear_instance()
    world = World()
    await world.initialize_simulation_context_async()

    world.scene.add_default_ground_plane()
    assets_root_path = get_assets_root_path()
    jetbot_asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
    my_jetbot = world.scene.add(
        WheeledRobot(
            prim_path="/World/Jetbot",
            name="my_jetbot",
            wheel_dof_names=["left_wheel_joint", "right_wheel_joint"],
            create_robot=True,
            usd_path=jetbot_asset_path,
            position=np.array([-1.5, -1.5, 0]),
        )
    )
    await world.reset_async()
    await world.play_async()

    wheel_radius = 0.03
    wheel_base = 0.1125
    controller = DifferentialController("test_controller", wheel_radius, wheel_base)
    linear_speed = 0.3
    angular_speed = 1.0

    command = [linear_speed, angular_speed]
    my_jetbot.apply_wheel_actions(controller.forward(command))

    await asyncio.sleep(5.0)  # Run for 5 seconds
    world.pause()


# Run the example
asyncio.ensure_future(differential_controller_example())
