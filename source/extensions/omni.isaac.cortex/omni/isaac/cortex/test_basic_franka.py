# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

import omni
from omni.isaac.core import World
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.franka import Franka
from omni.isaac.core.utils.stage import add_reference_to_stage


def main():
    world = World(stage_units_in_meters=0.01)
    world.scene.add_default_ground_plane()

    prim_path = "/cortex/world/franka"
    robot_name = "franka"
    from omni.isaac.franka import Franka

    robot = Franka(prim_path=prim_path, name=robot_name)
    world.scene.add(robot)
    world.reset()

    retracted_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0])
    robot.set_joint_positions(retracted_config)

    target_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0]) + np.pi / 2

    a = 0.0
    s = 1.0
    while simulation_app.is_running():
        config = (1.0 - a) * retracted_config + a * target_config
        robot.set_joint_positions(config)
        world.step(render=True)

        a += s * 0.01
        if a > 1 or a < 0.0:
            s *= -1.0


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nException caught.")
        import traceback

        traceback.print_exc()
    finally:
        simulation_app.close()
        print("<done>")
