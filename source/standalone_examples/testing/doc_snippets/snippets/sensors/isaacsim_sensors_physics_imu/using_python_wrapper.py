import numpy as np
from isaacsim.sensors.physics import IMUSensor

IMUSensor(
    prim_path="/World/Cube/Imu",
    name="imu",
    frequency=60,  # or, dt=1./60
    translation=np.array([0, 0, 0]),  # or, position=np.array([0, 0, 0]),
    orientation=np.array([1, 0, 0, 0]),
    linear_acceleration_filter_size=10,
    angular_velocity_filter_size=10,
    orientation_filter_size=10,
)
