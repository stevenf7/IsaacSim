import asyncio

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim


async def example():
    stage_utils.define_prim("/World/physicsScene", "PhysicsScene")
    GroundPlane("/World/groundPlane")

    # create three rigid cubes sitting on top of three others
    bottom_box_paths = [f"/World/bottom_box_{i+1}" for i in range(3)]
    top_box_paths = [f"/World/top_box_{i+1}" for i in range(3)]
    Cube(bottom_box_paths, sizes=2, colors=np.array([0.5, 0, 0]))
    Cube(top_box_paths, sizes=2, colors=np.array([0, 0, 0.5]))
    GeomPrim(bottom_box_paths + top_box_paths, apply_collision_apis=True)

    # Specify top boxes as filters to receive contact forces between the bottom and top boxes.
    bottom_box = RigidPrim(
        bottom_box_paths,
        masses=[1.0],
        positions=np.array([[0, 0, 1.0], [-5.0, 0, 1.0], [5.0, 0, 1.0]]),
        contact_filter_paths=top_box_paths,
        max_contact_count=30,
    )
    top_box = RigidPrim(
        top_box_paths,
        masses=[1.0],
        positions=np.array([[0.0, 0, 3.0], [-5.0, 0, 3.0], [5.0, 0, 3.0]]),
    )
    bottom_box.set_enabled_contact_tracking([True])
    top_box.set_enabled_contact_tracking([True])

    app_utils.play()
    await app_utils.update_app_async(steps=10)

    # net contact forces acting on the bottom boxes
    print(bottom_box.get_net_contact_forces().numpy())
    # contact forces between the top and the bottom boxes
    print(bottom_box.get_contact_force_matrix().numpy())
    app_utils.stop()


asyncio.ensure_future(example())
