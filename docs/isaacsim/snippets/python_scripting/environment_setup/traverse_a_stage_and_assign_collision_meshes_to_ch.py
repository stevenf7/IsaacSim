import omni
from omni.physx.scripts import utils
from pxr import Gf, Usd, UsdGeom

stage = omni.usd.get_context().get_stage()


def add_cube(stage, path, size: float = 10, offset: Gf.Vec3d = Gf.Vec3d(0, 0, 0)):
    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubeGeom.CreateSizeAttr(size)
    cubeGeom.AddTranslateOp().Set(offset)


### The following prims are added for illustrative purposes
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Torus")
# all prims under AddCollision will get collisions assigned
add_cube(stage, "/World/Cube_0", offset=Gf.Vec3d(100, 100, 0))
# create a prim nested under without a parent
add_cube(stage, "/World/Nested/Cube", offset=Gf.Vec3d(100, 0, 100))
###

# Traverse all prims in the stage starting at this path
curr_prim = stage.GetPrimAtPath("/")

for prim in Usd.PrimRange(curr_prim):
    # only process shapes and meshes
    if (
        prim.IsA(UsdGeom.Cylinder)
        or prim.IsA(UsdGeom.Capsule)
        or prim.IsA(UsdGeom.Cone)
        or prim.IsA(UsdGeom.Sphere)
        or prim.IsA(UsdGeom.Cube)
    ):
        # use a ConvexHull for regular prims
        utils.setCollider(prim, approximationShape="convexHull")
    elif prim.IsA(UsdGeom.Mesh):
        # "None" will use the base triangle mesh if available
        # Can also use "convexDecomposition", "convexHull", "boundingSphere", "boundingCube"
        utils.setCollider(prim, approximationShape="None")
    pass
pass
