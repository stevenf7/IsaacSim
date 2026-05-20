import isaacsim.core.experimental.utils.transform as transform_utils
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import XformPrim

# Create a cube mesh in the stage to demonstrate setting a world pose on a prim
cube = Cube("/World/Cube")

# Get the prim and set its world pose
orientation = transform_utils.euler_angles_to_quaternion([0.0, 290.0, 0.0], degrees=True)
XformPrim(cube.paths).set_world_poses(positions=[[0.10, 1.0, 1.5]], orientations=orientation)
