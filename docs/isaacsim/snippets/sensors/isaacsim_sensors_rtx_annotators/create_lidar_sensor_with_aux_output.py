import numpy as np
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor

# Set aux_output_level to BASIC (or higher) to enable emitterId and other auxiliary fields.
lidar = Lidar.create(
    path="/World/lidar",
    config="Example_Rotary",
    aux_output_level="BASIC",
    translations=np.array([0.0, 0.0, 1.0]),
    orientations=np.array([1.0, 0.0, 0.0, 0.0]),
)

# Create a LidarSensor with the generic-model-output annotator.
# Auxiliary fields are included in the GenericModelOutput buffer based on the aux_output_level.
sensor = LidarSensor(lidar, annotators=["generic-model-output"])
