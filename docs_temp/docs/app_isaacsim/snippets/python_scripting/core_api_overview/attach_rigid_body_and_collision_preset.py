import numpy as np
from isaacsim.core.api.objects import DynamicCuboid

DynamicCuboid(
    prim_path="/new_cube_2",
    name="cube_1",
    position=np.array([0, 0, 1.0]),
    scale=np.array([0.6, 0.5, 0.2]),
    size=1.0,
    color=np.array([255, 0, 0]),
)
