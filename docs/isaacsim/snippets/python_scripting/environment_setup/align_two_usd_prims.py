import isaacsim.core.experimental.utils.transform as transform_utils
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import XformPrim

# Create a cube
cube_a = Cube("/World/CubeA")
# change the cube pose
orientation = transform_utils.euler_angles_to_quaternion([0.0, 290.0, 0.0], degrees=True)
prim_a = XformPrim(cube_a.paths)
prim_a.set_world_poses(positions=[[0.10, 1.0, 1.5]], orientations=orientation)
# Create a second cube
cube_b = Cube("/World/CubeB")
# Get the transform of the first cube
positions, orientations = prim_a.get_world_poses()
# Set the pose of prim_b to that of prim_a
XformPrim(cube_b.paths).set_world_poses(positions=positions, orientations=orientations)
