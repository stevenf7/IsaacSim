# isort: skip_file
# -- Test setup --
import numpy as np
from isaacsim.core.cloner import Cloner, GridCloner
from isaacsim.core.experimental.utils.stage import get_current_stage
from pxr import UsdGeom

# -- End test setup --

# [introduction]
from isaacsim.core.cloner import Cloner  # import Cloner interface
from isaacsim.core.experimental.utils.stage import get_current_stage
from pxr import UsdGeom

# create our base environment with one cube
base_env_path = "/World/Cube_0"
UsdGeom.Cube.Define(get_current_stage(), base_env_path)

# create a Cloner instance
cloner = Cloner()

# generate 4 paths that begin with "/World/Cube" - path will be appended with _{index}
target_paths = cloner.generate_paths("/World/Cube", 4)

# clone the cube at target paths
cloner.clone(source_prim_path="/World/Cube_0", prim_paths=target_paths)
# [/introduction]

# [clone-at-positions]
import numpy as np

cube_positions = np.array([[0, 0, 0], [3, 0, 0], [6, 0, 0], [9, 0, 0]])

# clone the cube at target paths at specified positions
cloner.clone(source_prim_path="/World/Cube_0", prim_paths=target_paths, positions=cube_positions)
# [/clone-at-positions]

# [grid-cloner]
from isaacsim.core.cloner import GridCloner  # import GridCloner interface
from isaacsim.core.experimental.utils.stage import get_current_stage
from pxr import UsdGeom

# create our base environment with one cube
base_env_path = "/World/Cube_0"
UsdGeom.Cube.Define(get_current_stage(), base_env_path)

# create a GridCloner instance
cloner = GridCloner(spacing=3)

# generate 4 paths that begin with "/World/Cube" - path will be appended with _{index}
target_paths = cloner.generate_paths("/World/Cube", 4)

# clone the cube at target paths
cloner.clone(source_prim_path="/World/Cube_0", prim_paths=target_paths)
# [/grid-cloner]

# [accessing-cloned-objects]
# import the XformPrim interface from isaacsim.core.experimental.prims for APIs for Xform prims
import numpy as np
from isaacsim.core.experimental.prims import XformPrim

# retrieve a prim wrapping all 4 boxes by using a regex expression that matches the prim paths for all boxes
boxes = XformPrim("/World/Cube_.*")

# retrieve the global transforms of all boxes
#   - positions will be a vector of shape (4, 3) for X, Y, Z axes of translation
#   - orientations will be a vector of shape (4, 4) for W, X, Y, Z axes of quaternion
positions, orientations = boxes.get_world_poses()
positions = positions.numpy()
orientations = orientations.numpy()

# increase positions on the Z axis to move boxes up by 1.5 units
positions[:, 2] += 1.5
# apply the new positions
boxes.set_world_poses(positions, orientations)
# [/accessing-cloned-objects]

# [physics-replication-setup]
import numpy as np
from isaacsim.core.cloner import Cloner
from isaacsim.core.experimental.utils.stage import get_current_stage
from pxr import UsdGeom

base_env_path = "/World/Ants/Ant_0"
UsdGeom.Xform.Define(get_current_stage(), "/World/Ants")
UsdGeom.Cube.Define(get_current_stage(), base_env_path)

cloner = Cloner()
target_paths = cloner.generate_paths("/World/Ants/Ant", 4)
position_offsets = np.array([[0, 0, 0], [3, 0, 0], [6, 0, 0], [9, 0, 0]])
# [/physics-replication-setup]

# [physics-replication]
cloner.clone(
    source_prim_path="/World/Ants/Ant_0",
    prim_paths=target_paths,
    positions=position_offsets,
    replicate_physics=True,
    base_env_path="/World/Ants",
    root_path="/World/Ants/Ant_",
)
# [/physics-replication]

# [additional-parameters]
cloner.clone(
    source_prim_path="/World/Ants/Ant_0",
    prim_paths=target_paths,
    positions=position_offsets,
    replicate_physics=True,
    base_env_path="/World/Ants",
    root_path="/World/Ants/Ant_",
    copy_from_source=True,
)
# [/additional-parameters]

# -- Test cleanup --
