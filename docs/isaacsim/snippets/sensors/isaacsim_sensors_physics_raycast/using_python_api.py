import math

from isaacsim.sensors.experimental.physics import Raycast, RaycastSensor

# Generate a simple grid of ray directions for a solid state physics raycast sensor.
h_count, v_count = 10, 5
h_fov, v_fov = 60.0, 20.0
origins = []
directions = []
for vi in range(v_count):
    v_angle = math.radians(-v_fov / 2 + v_fov * vi / max(v_count - 1, 1))
    for hi in range(h_count):
        h_angle = math.radians(-h_fov / 2 + h_fov * hi / max(h_count - 1, 1))
        dx = math.cos(v_angle) * math.cos(h_angle)
        dy = math.cos(v_angle) * math.sin(h_angle)
        dz = math.sin(v_angle)
        origins.append([0.0, 0.0, 0.0])
        directions.append([dx, dy, dz])

sensor = RaycastSensor(
    Raycast.create(
        "/World/Sensors/Physics_Raycast_Sensor",
        min_range=0.4,
        max_range=100.0,
        ray_origins=origins,
        ray_directions=directions,
        output_frame="WORLD",
        translations=[[0.0, 0.0, 1.5]],
    )
)
