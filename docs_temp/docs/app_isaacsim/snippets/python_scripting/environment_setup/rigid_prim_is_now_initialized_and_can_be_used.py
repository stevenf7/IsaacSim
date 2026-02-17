import asyncio

from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.api.world import World
from isaacsim.core.prims import RigidPrim


async def init():
    if World.instance():
        World.instance().clear_instance()
    world = World()
    await world.initialize_simulation_context_async()
    world.scene.add_default_ground_plane(z_position=-1.0)
    cube = DynamicCuboid(prim_path="/World/cube_0")
    rigid_prim = RigidPrim(prim_paths_expr="/World/cube_[0-100]")
    # View classes are internally initialized when they are added to the scene and the world is reset
    world.scene.add(rigid_prim)
    await world.reset_async()
    # rigid_prim is now initialized and can be used


asyncio.ensure_future(init())
