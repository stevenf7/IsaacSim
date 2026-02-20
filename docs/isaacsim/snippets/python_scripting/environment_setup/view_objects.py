from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.api.world import World
from isaacsim.core.prims import RigidPrim

# View classes are initialized when they are added to the scene and the world is reset
world = World()
cube = DynamicCuboid(prim_path="/World/cube_0")
rigid_prim = RigidPrim(prim_paths_expr="/World/cube_[0-100]")
world.scene.add(rigid_prim)
world.reset()
# rigid_prim is now initialized and can be used
