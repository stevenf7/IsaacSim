import asyncio

import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim


async def example():
    stage_utils.define_prim("/World/physicsScene", "PhysicsScene")
    GroundPlane("/World/groundPlane", positions=[0.0, 0.0, -1.0])

    # create rigid cubes
    cube_paths = [f"/World/cube_{i}" for i in range(3)]
    Cube(cube_paths)
    GeomPrim(cube_paths, apply_collision_apis=True)

    # create the view object to batch manipulate the cubes
    rigid_prim = RigidPrim("/World/cube_[0-2]", masses=[1.0])
    # set world poses
    rigid_prim.set_world_poses(positions=np.array([[0, 0, 2], [0, -2, 2], [0, 2, 2]]))


asyncio.ensure_future(example())
