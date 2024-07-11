import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--num-robots", type=int, default=1, help="Number of robots")
parser.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs on machine.")
parser.add_argument("--num-frames", type=int, default=600, help="Number of frames to run benchmark for")
parser.add_argument(
    "--backend-type",
    default="OsmoKPIFile",
    choices=["LocalLogMetrics", "JSONFileMetrics", "OsmoKPIFile"],
    help="Benchmarking backend, defaults OsmoKPIFile",
)

args, unknown = parser.parse_known_args()

n_robot = args.num_robots
n_gpu = args.num_gpus
n_frames = args.num_frames

import numpy as np
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True, "max_gpu_count": n_gpu})

import asyncio
from functools import partial

import omni.isaac.core.utils.stage as stage_utils
import omni.physx as _physx
import omni.timeline
from omni.isaac.core import PhysicsContext
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core.utils.stage import open_stage_async, update_stage_async
from omni.isaac.core.utils.types import ArticulationAction
from omni.kit.viewport.utility import get_active_viewport

enable_extension("omni.isaac.benchmark.services")
from omni.isaac.benchmark.services import BaseIsaacBenchmark

# Create the benchmark
benchmark = BaseIsaacBenchmark(
    benchmark_name="benchmark_robots_ur10",
    workflow_metadata={
        "metadata": [
            {"name": "num_robots", "data": n_robot},
            {"name": "num_gpus", "data": n_gpu},
        ]
    },
    backend_type=args.backend_type,
)

# Something about this being in an array makes it work as a global variable inside the physics sub
timestep = [0]

observed_positions, observed_velocities = [], []
commanded_positions, commanded_velocities = [], []

# v_max is the maximum velocity that each joint will hit in its range of motion
v_max = np.array([2.09, 2.09, 3.14, 3.14, 3.14, 3.14])

# T is the period of each sinusoid
T = np.array([9.43, 9.43, 6.28, 6.28, 6.28, 6.28])

joint_indices = np.arange(6)

robot_path = "/ur10"


def get_clipped_joint_ranges(articulation):
    lower_limit = articulation.dof_properties["lower"]
    upper_limit = articulation.dof_properties["upper"]

    l = np.copy(lower_limit)
    u = np.copy(upper_limit)
    d = upper_limit - lower_limit
    mask = d > 2 * np.pi
    if np.any(mask):
        l[mask] = (upper_limit[mask] - lower_limit[mask]) / 2 + lower_limit[mask] - np.pi
        u[mask] = (upper_limit[mask] - lower_limit[mask]) / 2 + lower_limit[mask] + np.pi

    return l, u


def get_joint_commands(articulation, v_max, T, joint_indices):
    lower_joint_limits, upper_joint_limits = get_clipped_joint_ranges(articulation)

    lower_joint_limits = lower_joint_limits[joint_indices]
    upper_joint_limits = upper_joint_limits[joint_indices]

    p_0 = lower_joint_limits + (upper_joint_limits - lower_joint_limits) / 2

    position = lambda t: p_0 - v_max * T / np.pi * np.cos(np.pi * t / T)
    velocity = lambda t: v_max * np.sin(np.pi * t / T)

    return position, velocity


def on_physics_step(articulation, position_commands, velocity_commands, step):
    if position_commands is None:
        return
    timestep[0] += step
    if timestep[0] > 5:
        return

    observed_positions.append(articulation.get_joint_positions(joint_indices))
    observed_velocities.append(articulation.get_joint_velocities(joint_indices))

    position_command = position_commands(timestep[0])
    velocity_command = velocity_commands(timestep[0])

    commanded_positions.append(position_command)
    commanded_velocities.append(velocity_command)

    action = ArticulationAction(position_command, velocity_command, joint_indices=joint_indices)
    articulation.apply_action(action)


benchmark.set_phase("loading", start_recording_frametime=False, start_recording_runtime=True)

get_active_viewport().updates_enabled = False

robot_usd_path = "omniverse://ov-isaac-dev.nvidia.com/Isaac/Robots/UR10/ur10.usd"
stage = omni.usd.get_context().get_stage()
PhysicsContext(physics_dt=1.0 / 60.0)

robots = []
for i in range(n_robot):
    robot_prim_path = "/Robots/Robot_" + str(i)
    # position the robot
    MAX_IN_LINE = 10
    robot_position = np.array([-2 * (i % MAX_IN_LINE), -2 * np.floor(i / MAX_IN_LINE), 0])
    stage_utils.add_reference_to_stage(robot_usd_path, robot_prim_path)
    current_robot = Articulation(robot_prim_path)

    omni.kit.app.get_app().update()
    omni.kit.app.get_app().update()

    robots.append(current_robot)

timeline = omni.timeline.get_timeline_interface()
timeline.play()
omni.kit.app.get_app().update()

for robot in robots:
    robot.initialize()
    omni.kit.app.get_app().update()

    position_commands, velocity_commands = get_joint_commands(robot, v_max, T, joint_indices)
    _physxIFace = _physx.acquire_physx_interface()
    physx_subscription = _physxIFace.subscribe_physics_step_events(
        partial(on_physics_step, robot, position_commands, velocity_commands)
    )

    position_command = position_commands(0)
    velocity_command = velocity_commands(0)

    robot.set_joint_positions(position_command, joint_indices=joint_indices)

    commanded_positions.append(position_command)
    commanded_velocities.append(velocity_command)

omni.kit.app.get_app().update()
omni.kit.app.get_app().update()

benchmark.store_measurements()
# perform benchmark
benchmark.set_phase("benchmark")

for _ in range(0, n_frames):
    omni.kit.app.get_app().update()

benchmark.store_measurements()
benchmark.stop()

physics_subscription = None

timeline.stop()
simulation_app.close()
