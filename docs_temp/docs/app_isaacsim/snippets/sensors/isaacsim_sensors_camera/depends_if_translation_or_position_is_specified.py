import isaacsim.core.utils.prims as prim_utils
from isaacsim.sensors.camera import Camera

camera_prim = prim_utils.create_prim(
    prim_path="/World/camera",
    prim_type="Camera",
    # translation = ...
    # orientation = ...
)

camera = Camera(
    prim_path="/World/camera",
)
