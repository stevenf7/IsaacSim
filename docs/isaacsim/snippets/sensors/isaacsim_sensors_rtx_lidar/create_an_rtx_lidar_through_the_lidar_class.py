import numpy as np
from isaacsim.sensors.experimental.rtx import Lidar

# Create an RTX Lidar from a known sensor configuration.
lidar = Lidar.create(
    path="/World/lidar",
    config="Example_Rotary",
    translations=np.array([0.0, 0.0, 1.0]),
    orientations=np.array([1.0, 0.0, 0.0, 0.0]),
    attributes={"omni:sensor:Core:scanRateBaseHz": 20},
)
