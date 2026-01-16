import numpy as np
from isaacsim.core.prims import XFormPrim

translate_offset = np.array([[1.5, 1.2, 1.0]])
orientation_offset = np.array([[0.7, 0.7, 0, 1]])  # note this is in radians
scale = np.array([[1, 1.5, 0.2]])

stage = omni.usd.get_context().get_stage()
cube_in_coreapi = XFormPrim(prim_paths_expr="/test_cube")
cube_in_coreapi.set_world_poses(translate_offset, orientation_offset)
cube_in_coreapi.set_local_scales(scale)
