from isaacsim.sensors.physics import EffortSensor


# Input Param: List of past EsSensorReading, time of the expected sensor reading
def interpolation_function(data, time):
    interpolated_reading = EsSensorReading()
    # do interpolation
    return interpolated_reading


# get sensor readings
reading = sensor.get_sensor_reading(interpolation_function)
