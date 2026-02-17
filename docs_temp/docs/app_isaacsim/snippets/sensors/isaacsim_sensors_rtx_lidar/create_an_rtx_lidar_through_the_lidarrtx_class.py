import numpy as np
import omni
from isaacsim.sensors.rtx import LidarRtx

sensor_attributes = {"omni:sensor:Core:scanRateBaseHz": 20}

# Create the RTX Lidar with the specified attributes.
sensor = LidarRtx(
    prim_path="/lidar",
    translation=np.array([0.0, 0.0, 1.0]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
    config_file_name="Example_Rotary",
    **sensor_attributes,
)
