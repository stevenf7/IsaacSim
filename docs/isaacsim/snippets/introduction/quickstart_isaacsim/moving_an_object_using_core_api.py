# -- Test setup --
import numpy as np
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import XformPrim

Cube(paths="/test_cube", positions=[0, 0, 0.5])
# -- End test setup --

translate_offset = [1.5, 1.2, 1.0]
orientation_offset = [0.7, 0.7, 0, 1]
scale = [1, 1.5, 0.2]

cube_prim = XformPrim(paths="/test_cube")
cube_prim.set_world_poses(translate_offset, orientation_offset)
cube_prim.set_local_scales(scale)
