# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp

import argparse

parser = argparse.ArgumentParser("demo_leonardo")
parser.add_argument(
    "--behavior",
    type=str,
    default="behaviors/franka/block_stacking_behavior.py",
    help="Which behavior to run. See behavior/franka for available behavior files.",
)
args, _ = parser.parse_known_args()

simulation_app = SimulationApp({"headless": False})

from collections import OrderedDict
import numpy as np

import omni
from omni.isaac.core.objects import DynamicCuboid, VisualCuboid
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.materials import OmniPBR, VisualMaterial, PreviewSurface
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.utils.prims import delete_prim

from omni.isaac.cortex.df import DfNetwork
from omni.isaac.cortex.cortex_object import CortexObject
from omni.isaac.cortex.cortex_world import CortexWorld, LogicalStateMonitor, Behavior
from omni.isaac.cortex.robot import CortexFranka, add_franka_to_stage
from omni.isaac.cortex.tools import SteadyRate
from omni.isaac.cortex.cortex_utils import load_behavior_module


class LeonardoAssets:
    def __init__(self):
        self.assets_root_path = get_assets_root_path()
        if self.assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.franka_table_usd = self.assets_root_path + "/Isaac/Samples/Leonardo/Stage/franka_block_stacking.usd"
        self.franka_ghost_usd = self.assets_root_path + "/Isaac/Samples/Leonardo/Robots/franka_ghost.usd"
        self.background_usd = self.assets_root_path + "/Isaac/Environments/Grid/gridroom_curved.usd"
        self.rubiks_cube_usd = self.assets_root_path + "/Isaac/Props/Rubiks_Cube/rubiks_cube.usd"
        self.red_cube_usd = self.assets_root_path + "/Isaac/Props/Blocks/red_block.usd"
        self.yellow_cube_usd = self.assets_root_path + "/Isaac/Props/Blocks/yellow_block.usd"
        self.green_cube_usd = self.assets_root_path + "/Isaac/Props/Blocks/green_block.usd"
        self.blue_cube_usd = self.assets_root_path + "/Isaac/Props/Blocks/blue_block.usd"

        self.cubes = OrderedDict()
        self.cubes["Red"] = self.red_cube_usd
        self.cubes["Yellow"] = self.yellow_cube_usd
        self.cubes["Green"] = self.green_cube_usd
        self.cubes["Blue"] = self.blue_cube_usd


def main():
    world = CortexWorld()

    leonardo_assets = LeonardoAssets()
    add_reference_to_stage(usd_path=leonardo_assets.franka_table_usd, prim_path="/World/LeonardoTable")
    add_reference_to_stage(usd_path=leonardo_assets.background_usd, prim_path="/World/Background")
    background_prim = XFormPrim("/World/Background", position=[0.0, -4.0, -1.0325])

    # TODO: just wrapping the stage's Franka sometimes doesn't work. Fingers sometimes penetrate the blocks.
    # Are the assets different?
    delete_prim("/World/LeonardoTable/Franka/panda")
    robot = world.add_robot(add_franka_to_stage(name="robot", prim_path="/World/LeonardoTable/Franka/panda"))
    # robot = world.add_robot(CortexFranka(name="robot", prim_path="/World/LeonardoTable/Franka/panda"))

    width = 0.0515
    for ((name, usd), (i, x)) in zip(leonardo_assets.cubes.items(), enumerate(np.linspace(0.3, 0.7, 4))):
        prim_path = "/World/Blocks/{}".format(name)
        add_reference_to_stage(usd_path=usd, prim_path=prim_path)

        # TODO: hack -- Move the blocks down. We're just using the materials of these blocks.
        XFormPrim(name="{}Hidden".format(name), prim_path=prim_path + "/Cube", position=[x, 0.0, -0.5], visible=False)

        material = PreviewSurface(
            prim_path="/World/Blocks/{}/Materials/{}".format(name, name), name="{}_material".format(name)
        )
        name = name + "Cube"
        prim_path = "/World/Blocks/{}".format(name)
        obj = DynamicCuboid(
            prim_path=prim_path,
            name=name,
            size=width,
            position=np.array([x, -0.3, width / 2]),
            visual_material=material,
        )
        robot.register_obstacle(CortexObject(world.scene.add(obj)))

    decider_network = load_behavior_module(args.behavior).make_decider_network(robot)
    world.add_logical_state_monitor(LogicalStateMonitor("ls_monitors", decider_network.context))
    world.add_behavior(Behavior("behavior", decider_network))

    world.step_loop_runner(simulation_app)

    simulation_app.close()


if __name__ == "__main__":
    main()
