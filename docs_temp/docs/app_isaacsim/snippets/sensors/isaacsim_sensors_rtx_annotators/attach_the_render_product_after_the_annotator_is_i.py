from isaacsim import SimulationApp

kit = SimulationApp()

import numpy as np
import omni
from isaacsim.sensors.rtx import LidarRtx

# Create the RTX Lidar with the specified attributes.
sensor = LidarRtx(
    prim_path="/lidar",
    translation=np.array([0.0, 0.0, 1.0]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
    config_file_name="Example_Rotary",
)

# Initialize the LidarRtx object, which creates a render product for the sensor.
sensor.initialize()

# Attach an annotator to the sensor.
sensor.attach_annotator("IsaacExtractRTXSensorPointCloudNoAccumulator")

# Play the timeline to initialize the OmniGraph associated with the annotator and render product,
# and begin collecting data.
timeline = omni.timeline.get_timeline_interface()
timeline.play()

# Collect data from the annotator on each simulation frame.
for _ in range(100):
    # Step the simulation
    kit.update()
    # Print data collected by each annotator attached to the sensor as a Python dict
    print(sensor.get_current_frame())

timeline.stop()
kit.close()
