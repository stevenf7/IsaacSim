import numpy as np

cube_positions = np.array([[0, 0, 0], [3, 0, 0], [6, 0, 0], [9, 0, 0]])

# clone the cube at target paths at specified positions
cloner.clone(source_prim_path="/World/Cube_0", prim_paths=target_paths, positions=cube_positions)
