import asyncio

import numpy as np
from isaacsim.core.api import World
from isaacsim.robot.wheeled_robots.controllers.holonomic_controller import HolonomicController
from isaacsim.robot.wheeled_robots.robots import WheeledRobot
from isaacsim.storage.native import get_assets_root_path


async def holonomic_controller_example():
    if World.instance():
        World.instance().clear_instance()
    world = World()
    await world.initialize_simulation_context_async()

    world.scene.add_default_ground_plane()
    assets_root_path = get_assets_root_path()
    kaya_asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Kaya/kaya.usd"
    my_kaya = world.scene.add(
        WheeledRobot(
            prim_path="/World/Kaya",
            name="my_kaya",
            wheel_dof_names=["axle_0_joint", "axle_1_joint", "axle_2_joint"],
            create_robot=True,
            usd_path=kaya_asset_path,
            position=np.array([-1, 0, 0]),
        )
    )
    await world.reset_async()
    await world.play_async()

    wheel_radius = [0.04, 0.04, 0.04]
    wheel_orientations = [[0, 0, 0, 1], [0.866, 0, 0, -0.5], [0.866, 0, 0, 0.5]]
    wheel_positions = [
        [-0.0980432, 0.000636773, -0.050501],
        [0.0493475, -0.084525, -0.050501],
        [0.0495291, 0.0856937, -0.050501],
    ]
    mecanum_angles = [90, 90, 90]
    command = [1.0, 1.0, 0.1]

    controller = HolonomicController(
        name="holonomic_controller",
        wheel_radius=wheel_radius,
        wheel_positions=wheel_positions,
        wheel_orientations=wheel_orientations,
        mecanum_angles=mecanum_angles,
    )
    my_kaya.apply_wheel_actions(controller.forward(command))

    await asyncio.sleep(5.0)  # Run for 5 seconds
    world.pause()


# Run the example
asyncio.ensure_future(holonomic_controller_example())
