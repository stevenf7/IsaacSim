# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

from collections import OrderedDict
import copy
import numpy as np
import random
import time

import omni
from omni.isaac.core.objects import DynamicCuboid, VisualCuboid, VisualCapsule, VisualSphere
from omni.isaac.core.prims import XFormPrim, RigidPrim
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.materials import OmniPBR, VisualMaterial, PreviewSurface
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage

from omni.isaac.cortex.cortex_rigid_prim import CortexRigidPrim
from omni.isaac.cortex.df import DfNetwork
from omni.isaac.cortex.cortex_world import CortexWorld, LogicalStateMonitor, Behavior
from omni.isaac.cortex.robot import CortexUr10
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq
from omni.isaac.cortex.cortex_utils import get_assets_root_path_or_die
from omni.isaac.cortex.tools import SteadyRate
from omni.isaac.core.utils.rotations import quat_to_rot_matrix

from omni.isaac.core.utils.math import normalized

import behaviors.ur10.bin_stacking_behavior as behavior


class Ur10Assets:
    def __init__(self):
        self.assets_root_path = get_assets_root_path_or_die()

        self.ur10_table_usd = (
            self.assets_root_path + "/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_short_suction.usd"
        )
        self.small_klt_usd = self.assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd"
        self.background_usd = self.assets_root_path + "/Isaac/Environments/Simple_Warehouse/warehouse.usd"
        self.rubiks_cube_usd = self.assets_root_path + "/Isaac/Props/Rubiks_Cube/rubiks_cube.usd"


def random_bin_spawn_transform():
    x = random.uniform(-0.15, 0.15)
    y = 1.5
    z = -0.15
    position = np.array([x, y, z])

    z = random.random() * 0.02 - 0.01
    w = random.random() * 0.02 - 0.01
    norm = np.sqrt(z ** 2 + w ** 2)
    quat = math_util.Quaternion([w / norm, 0, 0, z / norm])
    if random.random() > 0.5:
        print("<flip>")
        # flip the bin so it's upside down
        quat = quat * math_util.Quaternion([0, 0, 1, 0])
    else:
        print("<no flip>")

    return position, quat.vals


class BinStackingTask(BaseTask):
    def __init__(self, env_path, assets):
        super().__init__("bin_stacking")
        self.assets = assets

        self.max_bins = 36
        self.env_path = "/World/Ur10Table"
        self.bins = []
        self.stashed_bins = []
        self.on_conveyer = None

    def set_up_scene(self, scene) -> None:
        """ Add all bins, but stash them off to make them invisible.
        """
        super().set_up_scene(scene)

        print("BinStackingTask: setting up scene")

        bin_paths = [self.env_path + "/bins/bin_{}".format(i) for i in range(self.max_bins)]
        for i, prim_path in enumerate(bin_paths):
            print("{}) {}".format(i, prim_path))
            add_reference_to_stage(usd_path=self.assets.small_klt_usd, prim_path=prim_path)
            position = np.array([-50000 - 50 * i, 150, 0])  # Set the default position to be stashed way off
            rigid_bin = CortexRigidPrim(name="bin_{}".format(i), prim_path=prim_path, position=position)
            self.bins.append(self.scene.add(rigid_bin))

    def _spawn_bin(self, rigid_bin):
        x, q = random_bin_spawn_transform()
        rigid_bin.set_world_pose(position=x, orientation=q)
        rigid_bin.set_linear_velocity(np.array([0, -0.30, 0]))
        rigid_bin.set_visibility(True)
        rigid_bin.enable_rigid_body_physics()

    def post_reset(self) -> None:
        print("BinStackingTask: post reset")
        self.stashed_bins.clear()
        for i, rigid_bin in enumerate(self.bins):
            rigid_bin.disable_rigid_body_physics()
            rigid_bin.set_visibility(False)
            self.stashed_bins.append(rigid_bin)

    def pre_step(self, time_step_index, simulation_time) -> None:
        """ Spawn a new randomly oriented bin if the previous bin has been placed.
        """
        if self.on_conveyer is None:
            if len(self.stashed_bins) > 0:
                print("BinStackingTask: spawning new bin")
                self.on_conveyer = self.stashed_bins.pop(0)
                self._spawn_bin(self.on_conveyer)
                return
            else:
                # done
                return
        else:
            (x, y, z), _ = self.on_conveyer.get_world_pose()
            is_on_conveyer = y > 0.0 and -0.4 < x and x < 0.4
            if not is_on_conveyer:
                self.on_conveyer = None
            return


def main():
    world = CortexWorld()

    env_path = "/World/Ur10Table"
    ur10_assets = Ur10Assets()
    add_reference_to_stage(usd_path=ur10_assets.ur10_table_usd, prim_path=env_path)
    add_reference_to_stage(usd_path=ur10_assets.background_usd, prim_path="/World/Background")
    background_prim = XFormPrim(
        "/World/Background", position=[10.00, 2.00, -1.18180], orientation=[0.7071, 0, 0, 0.7071]
    )
    robot = world.add_robot(CortexUr10(name="robot", prim_path="{}/ur10".format(env_path)))

    obs = world.scene.add(
        VisualSphere(
            "/World/Ur10Table/Obstacles/FlipStationSphere",
            name="flip_station_sphere",
            position=np.array([0.73, 0.76, -0.13]),
            radius=0.2,
            visible=False,
        )
    )
    robot.register_obstacle(obs)
    obs = world.scene.add(
        VisualSphere(
            "/World/Ur10Table/Obstacles/NavigationDome",
            name="navigation_dome_obs",
            position=[-0.031, -0.018, -1.086],
            radius=1.1,
            visible=False,
        )
    )
    robot.register_obstacle(obs)

    az = np.array([1.0, 0.0, -0.3])
    ax = np.array([0.0, 1.0, 0.0])
    ay = np.cross(az, ax)
    R = math_util.pack_R(ax, ay, az)
    quat = math_util.matrix_to_quat(R)
    obs = world.scene.add(
        VisualCapsule(
            "/World/Ur10Table/Obstacles/NavigationBarrier",
            name="navigation_barrier_obs",
            position=[0.471, 0.276, -0.463 - 0.1],
            orientation=quat,
            radius=0.5,
            height=0.9,
            visible=False,
        )
    )
    robot.register_obstacle(obs)

    obs = world.scene.add(
        VisualCapsule(
            "/World/Ur10Table/Obstacles/NavigationFlipStation",
            name="navigation_flip_station_obs",
            position=np.array([0.766, 0.755, -0.5]),
            radius=0.5,
            height=0.5,
            visible=False,
        )
    )
    robot.register_obstacle(obs)

    world.add_task(BinStackingTask(env_path, ur10_assets))
    world.add_decider_network(behavior.make_decider_network(robot))

    world.run(simulation_app)
    simulation_app.close()


if __name__ == "__main__":
    main()
