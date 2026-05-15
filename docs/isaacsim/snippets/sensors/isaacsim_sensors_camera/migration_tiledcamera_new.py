import numpy as np
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import RtxCamera, TiledCameraSensor

# Author two camera prims (the explicit-list replacement for `prim_paths_expr="..."`).
RtxCamera("/World/env_0/Camera", positions=np.array([[0.0, 0.0, 5.0]]))
RtxCamera("/World/env_1/Camera", positions=np.array([[2.0, 0.0, 5.0]]))

# Optional reference geometry so the cameras have something to render.
Cube("/World/env_0/cube", positions=np.array([[0.0, 0.0, 0.0]]))
Cube("/World/env_1/cube", positions=np.array([[2.0, 0.0, 0.0]]))

tiled = TiledCameraSensor(
    paths=["/World/env_0/Camera", "/World/env_1/Camera"],
    resolution=(256, 256),
    annotators=["rgb"],
)
data, info = tiled.get_data("rgb", tiled=True)
