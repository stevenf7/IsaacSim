from isaacsim.sensors.experimental.physics import ImuSensorBackend

_imu_sensor_backend = ImuSensorBackend("/World/Cube/Imu")
_imu_sensor_backend.get_sensor_reading(read_gravity=False)
