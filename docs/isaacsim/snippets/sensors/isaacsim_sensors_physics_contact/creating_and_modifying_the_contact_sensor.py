from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import numpy as np
import omni.usd
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from pxr import UsdPhysics

# Create physics scene
stage = omni.usd.get_context().get_stage()
UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")

# Add ground plane and a dynamic cube with collision and rigid body
GroundPlane("/World/groundPlane", sizes=10, colors=np.array([0.5, 0.5, 0.5]))
Cube(
    "/World/Cube",
    positions=np.array([-0.5, -0.2, 1.0]),
    scales=np.array([0.5, 0.5, 0.5]),
    colors=np.array([0.2, 0.3, 0.0]),
)
RigidPrim("/World/Cube")
GeomPrim("/World/Cube", apply_collision_apis=True)
