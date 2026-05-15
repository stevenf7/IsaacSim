import numpy as np
from isaacsim.sensors.rtx import LidarRtx

sensor = LidarRtx(
    prim_path="/World/Lidar",
    config_file_name="Example_Rotary",
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
)
frame = sensor.get_current_frame()
