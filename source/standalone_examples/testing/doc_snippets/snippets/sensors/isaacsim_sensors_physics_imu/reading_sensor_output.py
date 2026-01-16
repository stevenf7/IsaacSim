from isaacsim.sensors.physics import _sensor

_imu_sensor_interface = _sensor.acquire_imu_sensor_interface()
_imu_sensor_interface.get_sensor_reading("/World/Cube/Imu", use_latest_data=True, read_gravity=True)
