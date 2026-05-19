# -- Add a ground plane --
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.objects import GroundPlane

stage_utils.create_new_stage()
GroundPlane("/World/GroundPlane", positions=[0, 0, 0])
# -- End add a ground plane --

# -- Add a light source --
from isaacsim.core.experimental.objects import DistantLight

distant_light = DistantLight("/DistantLight")
distant_light.set_intensities(300)
# -- End add a light source --

# -- Add visual cubes with the Core API --
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube

yellow_material = PreviewSurfaceMaterial("/Materials/yellow")
yellow_material.set_input_values("diffuseColor", [1.0, 1.0, 0.0])

cyan_material = PreviewSurfaceMaterial("/Materials/cyan")
cyan_material.set_input_values("diffuseColor", [0.0, 1.0, 1.0])

visual_cube = Cube(
    paths="/visual_cube",
    positions=[0, 0.5, 0.5],
    sizes=0.3,
)
visual_cube.apply_visual_materials(yellow_material)

test_cube = Cube(
    paths="/test_cube",
    positions=[0, -0.5, 0.5],
    sizes=0.3,
)
test_cube.apply_visual_materials(cyan_material)
# -- End add visual cubes with the Core API --

# -- Add a visual cube with the raw USD API --
import omni.usd
from pxr import Gf, UsdGeom

stage = omni.usd.get_context().get_stage()

path = "/visual_cube_usd"
cube_geom = UsdGeom.Cube.Define(stage, path)
cube_prim = stage.GetPrimAtPath(path)
size = 0.5
offset = Gf.Vec3f(1.5, -0.2, 1.0)
cube_geom.CreateSizeAttr(size)
if not cube_prim.HasAttribute("xformOp:translate"):
    UsdGeom.Xformable(cube_prim).AddTranslateOp().Set(offset)
else:
    cube_prim.GetAttribute("xformOp:translate").Set(offset)
# -- End add a visual cube with the raw USD API --

# -- Add physics and collision to a new cube --
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

red_material = PreviewSurfaceMaterial("/Materials/red")
red_material.set_input_values("diffuseColor", [1.0, 0.0, 0.0])

dynamic_cube = Cube(
    paths="/dynamic_cube",
    positions=[0, -1.0, 1.0],
    sizes=0.3,
    scales=[0.6, 0.5, 0.2],
)
dynamic_cube.apply_visual_materials(red_material)
RigidPrim(paths="/dynamic_cube")
GeomPrim(paths="/dynamic_cube", apply_collision_apis=True)
# -- End add physics and collision to a new cube --

# -- Add physics and collision to an existing cube --
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

RigidPrim(paths="/test_cube")
GeomPrim(paths="/test_cube", apply_collision_apis=True)
# -- End add physics and collision to an existing cube --

# -- Move an object with the Core API --
from isaacsim.core.experimental.prims import XformPrim

translate_offset = [1.5, 1.2, 1.0]
orientation_offset = [0.7, 0.7, 0, 1]
scale = [1, 1.5, 0.2]

cube_prim = XformPrim(paths="/test_cube")
cube_prim.set_world_poses(translate_offset, orientation_offset)
cube_prim.set_local_scales(scale)
# -- End move an object with the Core API --

# -- Move an object with the raw USD API --
import omni.usd
from pxr import Gf, UsdGeom

stage = omni.usd.get_context().get_stage()
cube_prim = stage.GetPrimAtPath("/visual_cube_usd")
translate_offset = Gf.Vec3f(1.5, -0.2, 1.0)
rotate_offset = Gf.Vec3f(90, -90, 180)  # Note this is in degrees.
scale = Gf.Vec3f(1, 1.5, 0.2)

if not cube_prim.HasAttribute("xformOp:translate"):
    UsdGeom.Xformable(cube_prim).AddTranslateOp().Set(translate_offset)
else:
    cube_prim.GetAttribute("xformOp:translate").Set(translate_offset)

if not cube_prim.HasAttribute("xformOp:rotateXYZ"):
    UsdGeom.Xformable(cube_prim).AddRotateXYZOp().Set(rotate_offset)
else:
    cube_prim.GetAttribute("xformOp:rotateXYZ").Set(rotate_offset)

if not cube_prim.HasAttribute("xformOp:scale"):
    UsdGeom.Xformable(cube_prim).AddScaleOp().Set(scale)
else:
    cube_prim.GetAttribute("xformOp:scale").Set(scale)
# -- End move an object with the raw USD API --
