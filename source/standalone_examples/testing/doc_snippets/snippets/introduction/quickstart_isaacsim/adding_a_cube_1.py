from isaacsim.core.prims import RigidPrim

RigidPrim("/test_cube")

from isaacsim.core.prims import GeometryPrim

prim = GeometryPrim("/test_cube")
prim.apply_collision_apis()
