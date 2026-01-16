import numpy as np
from isaacsim.core.prims.prim import Prim
from isaacsim.core.prims.xform_prim import XformPrim

translate_offset = np.array([[1.5, -0.2, 1.0]])
rotate_offset = np.array([[90, -90, 180]])
scale = np.array([[1, 1.5, 0.2]])

cube_in_coreapi = XformPrim(Prim(prim_paths_expr="/test_cube"))
cube_in_coreapi.set_world_poses(translate_offset, rotate_offset)
cube_in_coreapi.set_scales(scale)
