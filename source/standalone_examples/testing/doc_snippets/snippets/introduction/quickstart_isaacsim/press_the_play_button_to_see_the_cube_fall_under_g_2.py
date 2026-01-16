import numpy as np
from isaacsim.core.api.objects import VisualCuboid

VisualCuboid(
    prim_path="/visual_cube",
    name="visual_cube",
    position=np.array([0, 0.5, 0.5]),
    size=0.3,
    color=np.array([255, 255, 0]),
)
VisualCuboid(
    prim_path="/test_cube",
    name="test_cube",
    position=np.array([0, -0.5, 0.5]),
    size=0.3,
    color=np.array([0, 255, 255]),
)
