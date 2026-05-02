from isaacsim.sensors.experimental.physics import Raycast, RaycastSensor

sensor = RaycastSensor(
    Raycast.create(
        "/World/Sensors/Physics_Raycast_Sensor",
        ray_origins=[[0.0, 0.0, 0.0]],
        ray_directions=[[1.0, 0.0, 0.0]],
    )
)
reading = sensor.get_sensor_reading()

if reading.is_valid:
    print(f"Ray count: {reading.ray_count}")
    print(f"Depths: {reading.depths}")
    print(f"Hit positions: {reading.hit_positions}")
    print(f"Hit normals: {reading.hit_normals}")
