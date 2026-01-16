import numpy as np
from isaacsim.core.api.objects import DynamicCuboid

DynamicCuboid(
    prim_path="/dynamic_cube",
    name="dynamic_cube",
    position=np.array([0, -1.0, 1.0]),
    scale=np.array([0.6, 0.5, 0.2]),
    size=1.0,
    color=np.array([255, 0, 0]),
)
