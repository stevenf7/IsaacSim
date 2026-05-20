from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

# Create a cube mesh in the stage
cube = Cube("/World/Cube")
# Enable physics on prim
# If a tighter collision approximation is desired use convexDecomposition instead of convexHull
geom_prim = GeomPrim(cube.paths, apply_collision_apis=True)
geom_prim.set_collision_approximations(["convexDecomposition"])
RigidPrim(cube.paths)
