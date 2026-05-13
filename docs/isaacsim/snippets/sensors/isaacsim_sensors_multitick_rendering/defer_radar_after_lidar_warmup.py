from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True, "enable_motion_bvh": True})

import carb
import numpy as np
import omni
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import (
    Lidar,
    LidarSensor,
    Radar,
    RadarSensor,
    parse_generic_model_output_data,
)

Cube("/cube", sizes=2.0, positions=np.array([10.0, 0.0, 0.0]))

# Lidars: full wrap pre-play (USD prim + render product + annotators).
lidar_sensor_1 = LidarSensor(Lidar("/lidar_1"), annotators=["generic-model-output"])
lidar_sensor_2 = LidarSensor(Lidar("/lidar_2"), annotators=["generic-model-output"])

# Radar: USD authoring object only. Defer the RadarSensor wrap until after the
# Lidar frames-in-flight slots have stabilized post-play.
radar = Radar("/radar")

# Start playback and let the Lidars warm up for a few frames before wrapping
# the Radar. 5 frames is one full rotation of the default 3-slot
# frames-in-flight buffer plus a small margin; heavier scenes may need more.
timeline = omni.timeline.get_timeline_interface()
timeline.play()
for _ in range(5):
    simulation_app.update()

# Now safe to wrap the Radar. This call creates the Radar's render product and
# binds annotators - the operation that would open the FIF race window if done
# concurrently with Lidar attachment.
radar_sensor = RadarSensor(radar, annotators=["generic-model-output"])

# Continue running and verify every sensor is producing output.
for _ in range(60):
    simulation_app.update()

    for sensor, name in [
        (lidar_sensor_1, "lidar_1"),
        (lidar_sensor_2, "lidar_2"),
        (radar_sensor, "radar"),
    ]:
        data, _ = sensor.get_data("generic-model-output")
        gmo = parse_generic_model_output_data(data)
        carb.log_warn(f"{name}: numElements={gmo.numElements}")

timeline.stop()
simulation_app.close()
