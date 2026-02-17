import asyncio

import omni
from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.stage import (
    add_reference_to_stage,
    create_new_stage_async,
    get_current_stage,
)
from isaacsim.storage.native import get_assets_root_path
from pxr import UsdPhysics


async def joint_force():
    World.clear_instance()
    await create_new_stage_async()
    my_world = World(stage_units_in_meters=1.0, backend="torch", device="cpu")
    await my_world.initialize_simulation_context_async()
    await omni.kit.app.get_app().next_update_async()
    assets_root_path = get_assets_root_path()
    asset_path = assets_root_path + "/Isaac/Robots/IsaacSim/Ant/ant.usd"
    add_reference_to_stage(usd_path=asset_path, prim_path="/World/Ant")
    await omni.kit.app.get_app().next_update_async()
    my_world.scene.add_default_ground_plane()
    arti_view = SingleArticulation("/World/Ant/torso")
    my_world.scene.add(arti_view)
    await my_world.reset_async(soft=False)
    stage = get_current_stage()

    sensor_joint_forces = arti_view.get_measured_joint_forces()
    sensor_actuation_efforts = arti_view.get_measured_joint_efforts()
    # Iterates through the joint names in the articulation, retrieves information about the joints and their associated links,
    # and creates a mapping between joint names and their corresponding link indices.
    joint_link_id = dict()
    for joint_name in arti_view._articulation_view.joint_names:
        joint_path = "/World/Ant/joints/" + joint_name
        joint = UsdPhysics.Joint.Get(stage, joint_path)
        body_1_path = joint.GetBody1Rel().GetTargets()[0]
        body_1_name = stage.GetPrimAtPath(body_1_path).GetName()
        child_link_index = arti_view._articulation_view.get_link_index(body_1_name)
        joint_link_id[joint_name] = child_link_index

    print("joint link IDs", joint_link_id)
    print(sensor_joint_forces[joint_link_id["front_left_leg"]])
    print(sensor_actuation_efforts[joint_link_id["front_left_leg"]])


asyncio.ensure_future(joint_force())
