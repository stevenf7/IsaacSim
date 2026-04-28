# [create-python-api]
from isaacsim.sensors.experimental.physics import IMUSensor
from pxr import Gf

sensor = IMUSensor.create(
    "/World/Cube/imu_sensor",
    linear_acceleration_filter_size=10,
    angular_velocity_filter_size=10,
    orientation_filter_size=10,
    translation=Gf.Vec3d(0, 0, 0),
    orientation=Gf.Quatd(1, 0, 0, 0),
)
# [/create-python-api]

# [create-python-wrapper]
import numpy as np
from isaacsim.sensors.experimental.physics import IMUSensor

IMUSensor(
    prim_path="/World/Cube/Imu",
    name="imu",
    translation=np.array([0, 0, 0]),  # or, position=np.array([0, 0, 0]),
    orientation=np.array([1, 0, 0, 0]),
    linear_acceleration_filter_size=10,
    angular_velocity_filter_size=10,
    orientation_filter_size=10,
)
# [/create-python-wrapper]

# [reading-backend-gravity]
from isaacsim.sensors.experimental.physics import ImuSensorBackend

_imu_sensor_backend = ImuSensorBackend("/World/Cube/Imu")
_imu_sensor_backend.get_sensor_reading(read_gravity=True)
# [/reading-backend-gravity]

# [reading-backend-no-gravity]
from isaacsim.sensors.experimental.physics import ImuSensorBackend

_imu_sensor_backend = ImuSensorBackend("/World/Cube/Imu")
_imu_sensor_backend.get_sensor_reading(read_gravity=False)
# [/reading-backend-no-gravity]

# [reading-interpolation]
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
# [/reading-interpolation]
