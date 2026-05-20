import isaacsim.core.experimental.utils.transform as transform_utils
import omni
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import XformPrim

usd_context = omni.usd.get_context()

#### For testing purposes we create and select a prim
#### This section can be removed if you already have a prim selected
cube = Cube("/World/Cube")
# change the cube pose
orientation = transform_utils.euler_angles_to_quaternion([0.0, 290.0, 0.0], degrees=True)
XformPrim(cube.paths).set_world_poses(positions=[[0.10, 1.0, 1.5]], orientations=orientation)
omni.usd.get_context().get_selection().set_prim_path_selected(cube.paths[0], True, True, True, False)
####

# Get list of selected primitives
selected_prims = usd_context.get_selection().get_selected_prim_paths()
# Loop through all prims and print their transforms
for prim_path in selected_prims:
    print("Selected", prim_path)
    positions, orientations = XformPrim(prim_path).get_world_poses()
    rotation_matrices = transform_utils.quaternion_to_rotation_matrix(orientations)
    print("Translation: ", positions.numpy()[0])
    print("Rotation: ", orientations.numpy()[0])
    print("Rotation matrix:", rotation_matrices.numpy()[0])
