import omni
from omni.physx.scripts import utils

# Create a cube mesh in the stage
stage = omni.usd.get_context().get_stage()
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
# Get the prim
cube_prim = stage.GetPrimAtPath(path)
# Enable physics on prim
# If a tighter collision approximation is desired use convexDecomposition instead of convexHull
utils.setRigidBody(cube_prim, "convexHull", False)
