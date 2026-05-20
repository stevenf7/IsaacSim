import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.objects import Cube, Mesh
from isaacsim.core.experimental.prims import GeomPrim
from pxr import Usd, UsdGeom

stage = stage_utils.get_current_stage()


def add_cube(path, size: float = 10, offset=None):
    if offset is None:
        offset = [0.0, 0.0, 0.0]
    Cube(path, sizes=size, positions=offset)


### The following prims are added for illustrative purposes
Mesh("/World/Torus", primitives="Torus")
# all prims under AddCollision will get collisions assigned
add_cube("/World/Cube_0", offset=[100.0, 100.0, 0.0])
# create a prim nested under without a parent
stage_utils.define_prim("/World/Nested", "Xform")
add_cube("/World/Nested/Cube", offset=[100.0, 0.0, 100.0])
###

# Traverse all prims in the stage starting at this path
curr_prim = stage.GetPrimAtPath("/")
shape_types = (UsdGeom.Cylinder, UsdGeom.Capsule, UsdGeom.Cone, UsdGeom.Sphere, UsdGeom.Cube)

for prim in Usd.PrimRange(curr_prim):
    # only process shapes and meshes
    if any(prim.IsA(shape_type) for shape_type in shape_types):
        # use a ConvexHull for regular prims
        geom_prim = GeomPrim(str(prim.GetPath()), apply_collision_apis=True)
        geom_prim.set_collision_approximations(["convexHull"])
    elif prim.IsA(UsdGeom.Mesh):
        # "none" will use the base triangle mesh if available
        # Can also use "convexDecomposition", "convexHull", "boundingSphere", "boundingCube"
        geom_prim = GeomPrim(str(prim.GetPath()), apply_collision_apis=True)
        geom_prim.set_collision_approximations(["none"])
