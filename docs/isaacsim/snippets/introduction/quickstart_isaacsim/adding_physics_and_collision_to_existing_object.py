# -- Test setup --
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

# Create a cube to add physics and collision to
Cube(paths="/test_cube", positions=[0, 0, 0.5])
# -- End test setup --

RigidPrim(paths="/test_cube")
GeomPrim(paths="/test_cube", apply_collision_apis=True)
