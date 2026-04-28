from isaacsim.sensors.experimental.physics import RaycastSensor

sensor = RaycastSensor(
    "/World/Sensors/My_Sensor",
    ray_origins=[[0, 0, 0], [0, 0, 0]],
    ray_directions=[[1, 0, 0], [0, 1, 0]],
    min_range=0.4,
    max_range=100.0,
    output_frame="WORLD",
)

# After simulation starts:
frame = sensor.get_current_frame()
print(f"Depths: {frame['depths']}")
print(f"Hit positions: {frame['hit_positions']}")
