# [create-python-api]
import numpy as np
from isaacsim.sensors.experimental.physics import IMU, IMUSensor

sensor = IMUSensor(
    IMU.create(
        "/World/Cube/imu_sensor",
        linear_acceleration_filter_size=10,
        angular_velocity_filter_size=10,
        orientation_filter_size=10,
        translations=np.array([[0.0, 0.0, 0.0]]),
        orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
    )
)
# [/create-python-api]

# [create-python-wrapper]
import numpy as np
from isaacsim.sensors.experimental.physics import IMU, IMUSensor

IMUSensor(
    IMU(
        "/World/Cube/Imu",
        translations=np.array([[0.0, 0.0, 0.0]]),  # or, positions=np.array([[0.0, 0.0, 0.0]]),
        orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
        linear_acceleration_filter_size=10,
        angular_velocity_filter_size=10,
        orientation_filter_size=10,
    )
)
# [/create-python-wrapper]

# [reading-backend-gravity]
from isaacsim.sensors.experimental.physics import IMUSensor

sensor = IMUSensor("/World/Cube/Imu")
sensor.get_sensor_reading(read_gravity=True)
# [/reading-backend-gravity]

# [reading-backend-no-gravity]
from isaacsim.sensors.experimental.physics import IMUSensor

sensor = IMUSensor("/World/Cube/Imu")
sensor.get_sensor_reading(read_gravity=False)
# [/reading-backend-no-gravity]

# [reading-frame]
import numpy as np
from isaacsim.sensors.experimental.physics import IMU, IMUSensor

sensor = IMUSensor(
    IMU(
        "/World/Cube/Imu",
        translations=np.array([[0.0, 0.0, 0.0]]),
        orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
        linear_acceleration_filter_size=10,
        angular_velocity_filter_size=10,
        orientation_filter_size=10,
    )
)

value = sensor.get_data()
print(value)
# [/reading-frame]
