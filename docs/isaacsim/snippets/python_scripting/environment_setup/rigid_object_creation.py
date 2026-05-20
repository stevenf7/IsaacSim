import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

stage_utils.define_prim("/World/physicsScene", "PhysicsScene")
GroundPlane("/World/groundPlane", sizes=10, colors=np.array([0.5, 0.5, 0.5]), templates=None)
cube = Cube(
    "/World/cube",
    positions=np.array([-0.5, -0.2, 1.0]),
    scales=np.array([0.5, 0.5, 0.5]),
    colors=np.array([0.2, 0.3, 0.0]),
)
RigidPrim(cube.paths, masses=[1.0])
GeomPrim(cube.paths, apply_collision_apis=True)
