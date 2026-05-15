import numpy as np
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor

sensor = LidarSensor(
    Lidar.create(
        "/World/Lidar",
        config="Example_Rotary",
        orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
    ),
    annotators=["generic-model-output"],
)
data, info = sensor.get_data("generic-model-output")
