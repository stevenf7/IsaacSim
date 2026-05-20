from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

cube = Cube("/World/cube_0")
GeomPrim(cube.paths, apply_collision_apis=True)
rigid_prim = RigidPrim("/World/cube_[0-100]", masses=[1.0])
# rigid_prim can now be used for USD-backed batched operations
