# import the XFormPrim interface from isaacsim.core.prims for APIs for XForm prims
from isaacsim.core.prims import XFormPrim

# retrieve a View containing all 4 boxes by using a wildcard expression that matches the prim paths for all boxes
boxes = XFormPrim(prim_paths_expr="/World/Cube_*")

# retrieve the global transforms of all boxes
#   - positions will be a vector of shape (4, 3) for X, Y, Z axes of translation
#   - orientations will be a vector of shape (4, 4) for W, X, Y, Z axes of quaternion
positions, orientations = boxes.get_world_poses()

# increase positions on the Z axis to move boxes up by 1.5 units
positions[:, 2] += 1.5
# apply the new positions
boxes.set_world_poses(positions, orientations)
