from isaacsim.sensors.experimental.physics import RaycastSensor

sensor = RaycastSensor("/World/Sensors/Physics_Raycast_Sensor")
reading = sensor.get_sensor_reading()

if reading.is_valid:
    print(f"Ray count: {reading.ray_count}")
    print(f"Depths: {reading.depths}")
    print(f"Hit positions: {reading.hit_positions}")
    print(f"Hit normals: {reading.hit_normals}")
