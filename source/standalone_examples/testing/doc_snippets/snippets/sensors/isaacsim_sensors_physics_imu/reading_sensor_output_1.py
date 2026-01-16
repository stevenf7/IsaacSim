from typing import List

from isaacsim.sensors.physics import _sensor


# Input Param: List of past IsSensorReadings, time of the expected sensor reading
def interpolation_function(data: List[_sensor.IsSensorReading], time: float) -> _sensor.IsSensorReading:
    interpolated_reading = _sensor.IsSensorReading()
    # do interpolation
    return interpolated_reading


_imu_sensor_interface = _sensor.acquire_imu_sensor_interface()
_imu_sensor_interface.get_sensor_reading(
    "/World/Cube/Imu", interpolation_function=interpolation_function, read_gravity=False
)
