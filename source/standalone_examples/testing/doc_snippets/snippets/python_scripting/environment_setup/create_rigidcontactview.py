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
    world.scene.add_default_ground_plane()

    # create three rigid cubes sitting on top of three others
    for i in range(3):
        DynamicCuboid(prim_path=f"/World/bottom_box_{i+1}", size=2, color=np.array([0.5, 0, 0]), mass=1.0)
        DynamicCuboid(prim_path=f"/World/top_box_{i+1}", size=2, color=np.array([0, 0, 0.5]), mass=1.0)

    # as before, create RigidContactView to manipulate bottom boxes but this time specify top boxes as filters to the view object
    # this allows receiving contact forces between the bottom boxes and top boxes
    bottom_box = RigidPrim(
        prim_paths_expr="/World/bottom_box_*",
        name="bottom_box",
        positions=np.array([[0, 0, 1.0], [-5.0, 0, 1.0], [5.0, 0, 1.0]]),
        contact_filter_prim_paths_expr=["/World/top_box_*"],
    )
    # create a RigidContactView to manipulate top boxes
    top_box = RigidPrim(
        prim_paths_expr="/World/top_box_*",
        name="top_box",
        positions=np.array([[0.0, 0, 3.0], [-5.0, 0, 3.0], [5.0, 0, 3.0]]),
        track_contact_forces=True,
    )

    world.scene.add(top_box)
    world.scene.add(bottom_box)
    await world.reset_async()

    # net contact forces acting on the bottom boxes
    print(bottom_box.get_net_contact_forces())
    # contact forces between the top and the bottom boxes
    print(bottom_box.get_contact_force_matrix())


asyncio.ensure_future(example())
