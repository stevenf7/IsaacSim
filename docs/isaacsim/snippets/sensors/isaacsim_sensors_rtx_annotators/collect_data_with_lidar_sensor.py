from isaacsim import SimulationApp

kit = SimulationApp()

import numpy as np
import omni
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor, parse_generic_model_output_data

# Create the RTX Lidar.
lidar = Lidar.create(
    path="/World/lidar",
    config="Example_Rotary",
    translations=np.array([0.0, 0.0, 1.0]),
    orientations=np.array([1.0, 0.0, 0.0, 0.0]),
)

# Create a LidarSensor to attach annotators and retrieve data.
sensor = LidarSensor(lidar, annotators=["generic-model-output"])

# Play the timeline to begin collecting data.
timeline = omni.timeline.get_timeline_interface()
timeline.play()

# Collect data from the sensor on each simulation frame.
for _ in range(100):
    kit.update()
    data, info = sensor.get_data("generic-model-output")
    if data is not None:
        gmo = parse_generic_model_output_data(data)
        print(f"Points: {gmo.numElements}")

timeline.stop()
kit.close()
