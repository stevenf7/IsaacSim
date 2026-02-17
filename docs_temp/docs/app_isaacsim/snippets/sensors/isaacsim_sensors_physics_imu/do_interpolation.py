import numpy as np
from isaacsim.sensors.experimental.physics import IMUSensor

sensor = IMUSensor(
    prim_path="/World/Cube/Imu",
    name="imu",
    translation=np.array([0, 0, 0]),
    orientation=np.array([1, 0, 0, 0]),
    linear_acceleration_filter_size=10,
    angular_velocity_filter_size=10,
    orientation_filter_size=10,
)

value = sensor.get_current_frame()
print(value)
