from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

cube = Cube("/World/Cube")
# Make it a rigid body
geom_prim = GeomPrim(cube.paths, apply_collision_apis=True)
geom_prim.set_collision_approximations(["convexHull"])

rigid_prim = RigidPrim(cube.paths)
rigid_prim.set_masses([10.0])
### Alternatively set the density
rigid_prim.set_densities([1000.0])
