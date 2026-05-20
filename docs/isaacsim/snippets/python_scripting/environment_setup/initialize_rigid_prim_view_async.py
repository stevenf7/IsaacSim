import asyncio

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim


async def init():
    stage_utils.define_prim("/World/physicsScene", "PhysicsScene")
    GroundPlane("/World/groundPlane", positions=[0.0, 0.0, -1.0])
    cube = Cube("/World/cube_0")
    GeomPrim(cube.paths, apply_collision_apis=True)
    rigid_prim = RigidPrim("/World/cube_[0-100]", masses=[1.0])
    app_utils.play()
    await app_utils.update_app_async()
    print("Physics tensor view initialized:", rigid_prim.is_physics_tensor_entity_valid())
    app_utils.stop()


asyncio.ensure_future(init())
