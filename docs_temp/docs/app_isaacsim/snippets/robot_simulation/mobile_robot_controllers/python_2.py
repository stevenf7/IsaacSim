import asyncio

import isaacsim.core.utils.stage as stage_utils
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.robots import Robot
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.robot.wheeled_robots.controllers.ackermann_controller import AckermannController
from isaacsim.storage.native import get_assets_root_path


async def ackermann_controller_example():
    if World.instance():
        World.instance().clear_instance()
    world = World()
    await world.initialize_simulation_context_async()
    world.scene.add_default_ground_plane()

    assets_root_path = get_assets_root_path()
    leatherback_asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Leatherback/leatherback.usd"
    leatherback_prim_path = "/World/Leatherback"
    stage_utils.add_reference_to_stage(leatherback_asset_path, leatherback_prim_path)
    my_leatherback = world.scene.add(Robot(prim_path=leatherback_prim_path, name="my_leatherback"))
    await world.reset_async()
    await world.play_async()

    # Steering joints (position control)
    steering_joint_names = [
        "Knuckle__Upright__Front_Left",
        "Knuckle__Upright__Front_Right",
    ]
    # Wheel joints (velocity control)
    wheel_joint_names = [
        "Wheel__Knuckle__Front_Left",
        "Wheel__Knuckle__Front_Right",
        "Wheel__Upright__Rear_Left",
        "Wheel__Upright__Rear_Right",
    ]

    steering_joint_indices = [my_leatherback.get_dof_index(name) for name in steering_joint_names]
    wheel_joint_indices = [my_leatherback.get_dof_index(name) for name in wheel_joint_names]

    wheel_base = 1.65
    track_width = 1.25
    wheel_radius = 0.25
    desired_forward_vel = 1.1  # rad/s
    desired_steering_angle = 0.1  # rad
    # Setting acceleration, steering velocity, and dt to 0 to instantly reach the target steering and velocity
    acceleration = 0.0  # m/s^2
    steering_velocity = 0.0  # rad/s
    dt = 0.0  # secs

    controller = AckermannController(
        "test_controller",
        wheel_base=wheel_base,
        track_width=track_width,
        front_wheel_radius=wheel_radius,
        back_wheel_radius=wheel_radius,
    )
    actions = controller.forward([desired_steering_angle, steering_velocity, desired_forward_vel, acceleration, dt])

    full_joint_positions = np.zeros(my_leatherback.num_dof)
    full_joint_positions[steering_joint_indices[0]] = actions.joint_positions[0]  # Left steering
    full_joint_positions[steering_joint_indices[1]] = actions.joint_positions[1]  # Right steering
    # Create full joint velocity array (for wheels)
    full_joint_velocities = np.zeros(my_leatherback.num_dof)
    full_joint_velocities[wheel_joint_indices[0]] = actions.joint_velocities[0]  # FL wheel
    full_joint_velocities[wheel_joint_indices[1]] = actions.joint_velocities[1]  # FR wheel
    full_joint_velocities[wheel_joint_indices[2]] = actions.joint_velocities[2]  # BL wheel
    full_joint_velocities[wheel_joint_indices[3]] = actions.joint_velocities[3]  # BR wheel

    # Apply combined action
    combined_action = ArticulationAction(joint_positions=full_joint_positions, joint_velocities=full_joint_velocities)
    my_leatherback.apply_action(combined_action)

    await asyncio.sleep(5.0)  # Run for 5 seconds
    world.pause()


# Run the example
asyncio.ensure_future(ackermann_controller_example())
