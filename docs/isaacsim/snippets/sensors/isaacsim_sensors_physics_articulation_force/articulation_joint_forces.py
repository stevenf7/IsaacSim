import asyncio

import omni
import omni.timeline
from isaacsim.core.experimental.objects import GroundPlane
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.experimental.utils.stage import (
    add_reference_to_stage,
    create_new_stage_async,
)
from isaacsim.storage.native import get_assets_root_path
from pxr import UsdPhysics


async def joint_force():
    await create_new_stage_async()
    await omni.kit.app.get_app().next_update_async()

    # Set up the physics scene
    stage = omni.usd.get_context().get_stage()
    UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")

    # Load the Ant robot and add a ground plane
    assets_root_path = get_assets_root_path()
    asset_path = assets_root_path + "/Isaac/Robots/IsaacSim/Ant/ant.usd"
    add_reference_to_stage(usd_path=asset_path, path="/World/Ant")
    GroundPlane("/World/GroundPlane")
    await omni.kit.app.get_app().next_update_async()

    # Wrap the articulation
    arti = Articulation("/World/Ant/torso")

    # Start the simulation so that the physics tensor API becomes available
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    await omni.kit.app.get_app().next_update_async()

    # Read 6D joint forces (forces and torques per link)
    forces, torques = arti.get_link_incoming_joint_force()
    # Read DOF projected joint forces (active force component per DOF)
    projected_forces = arti.get_dof_projected_joint_forces()

    # Convert to numpy for inspection
    forces_np = forces.numpy()
    torques_np = torques.numpy()
    projected_np = projected_forces.numpy()

    # Map joint names to their link indices using the built-in API
    print("Joint names:", arti.joint_names)
    print("Link names:", arti.link_names)

    # Get the link and joint index for front_left_leg
    link_idx = int(arti.get_link_indices("front_left_leg").numpy()[0])
    joint_idx = int(arti.get_joint_indices("front_left_leg").numpy()[0])

    print("front_left_leg link forces:", forces_np[0, link_idx])
    print("front_left_leg link torques:", torques_np[0, link_idx])
    print("front_left_leg projected force:", projected_np[0, joint_idx])

    timeline.stop()


asyncio.ensure_future(joint_force())
