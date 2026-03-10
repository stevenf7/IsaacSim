import omni
from pxr import Gf, PhysicsSchemaTools

stage = omni.usd.get_context().get_stage()
PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 100, Gf.Vec3f(0, 0, -100), Gf.Vec3f(1.0))
