import omni
from pxr import Gf, UsdGeom

usd_context = omni.usd.get_context()
stage = usd_context.get_stage()

#### For testing purposes we create and select a prim
#### This section can be removed if you already have a prim selected
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
cube_prim = stage.GetPrimAtPath(path)
# change the cube pose
xform = UsdGeom.Xformable(cube_prim)
transform = xform.AddTransformOp()
mat = Gf.Matrix4d()
mat.SetTranslateOnly(Gf.Vec3d(0.10, 1, 1.5))
mat.SetRotateOnly(Gf.Rotation(Gf.Vec3d(0, 1, 0), 290))
transform.Set(mat)
omni.usd.get_context().get_selection().set_prim_path_selected(path, True, True, True, False)
####

# Get list of selected primitives
selected_prims = usd_context.get_selection().get_selected_prim_paths()
# Get the current timecode
timeline = omni.timeline.get_timeline_interface()
timecode = timeline.get_current_time() * timeline.get_time_codes_per_seconds()
# Loop through all prims and print their transforms
for s in selected_prims:
    curr_prim = stage.GetPrimAtPath(s)
    print("Selected", s)
    pose = omni.usd.utils.get_world_transform_matrix(curr_prim, timecode)
    print("Matrix Form:", pose)
    print("Translation: ", pose.ExtractTranslation())
    q = pose.ExtractRotation().GetQuaternion()
    print("Rotation: ", q.GetReal(), ",", q.GetImaginary()[0], ",", q.GetImaginary()[1], ",", q.GetImaginary()[2])
