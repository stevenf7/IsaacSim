import asyncio

import numpy as np
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.api.world import World
from isaacsim.core.prims import RigidPrim


async def example():
    if World.instance():
        World.instance().clear_instance()
    world = World()
    await world.initialize_simulation_context_async()
    world.scene.add_default_ground_plane(z_position=-1.0)

    # create rigid cubes
    for i in range(3):
        DynamicCuboid(prim_path=f"/World/cube_{i}")

    # create the view object to batch manipulate the cubes
    rigid_prim = RigidPrim(prim_paths_expr="/World/cube_[0-2]")
    world.scene.add(rigid_prim)
    await world.reset_async()
    # set world poses
    rigid_prim.set_world_poses(positions=np.array([[0, 0, 2], [0, -2, 2], [0, 2, 2]]))


asyncio.ensure_future(example())
