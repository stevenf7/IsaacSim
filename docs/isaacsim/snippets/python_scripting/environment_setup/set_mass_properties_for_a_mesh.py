import omni
from omni.physx.scripts import utils
from pxr import UsdPhysics

stage = omni.usd.get_context().get_stage()
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
# Get the prim
cube_prim = stage.GetPrimAtPath(path)
# Make it a rigid body
utils.setRigidBody(cube_prim, "convexHull", False)

mass_api = UsdPhysics.MassAPI.Apply(cube_prim)
mass_api.CreateMassAttr(10)
### Alternatively set the density
mass_api.CreateDensityAttr(1000)
