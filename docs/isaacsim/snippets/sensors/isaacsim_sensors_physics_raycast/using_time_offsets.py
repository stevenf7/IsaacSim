import math

import omni.kit.commands
from pxr import Gf

# Generate rays for a rotating physics raycast sensor with time offsets.
# Each azimuthal column is assigned a time offset within the sweep period.
# Only rays whose offsets fall in the current physics step are fired.
v_count = 8
azimuth_steps = 36
v_fov = 30.0
rotation_rate = 1.0
period = 1.0 / rotation_rate

origins = []
directions = []
time_offsets = []
for ai in range(azimuth_steps):
    h_angle = math.radians(360.0 * ai / azimuth_steps)
    t_offset = period * ai / azimuth_steps
    for vi in range(v_count):
        v_angle = math.radians(-v_fov / 2 + v_fov * vi / max(v_count - 1, 1))
        dx = math.cos(v_angle) * math.cos(h_angle)
        dy = math.cos(v_angle) * math.sin(h_angle)
        dz = math.sin(v_angle)
        origins.append([0.0, 0.0, 0.0])
        directions.append([dx, dy, dz])
        time_offsets.append(t_offset)

success, sensor_prim = omni.kit.commands.execute(
    "IsaacSensorExperimentalCreateRaycastSensor",
    path="/Rotating_Physics_Raycast_Sensor",
    parent="/World/Sensors",
    min_range=0.4,
    max_range=100.0,
    ray_origins=origins,
    ray_directions=directions,
    ray_time_offsets=time_offsets,
    output_frame="WORLD",
    translation=Gf.Vec3d(0, 0, 1.5),
)
