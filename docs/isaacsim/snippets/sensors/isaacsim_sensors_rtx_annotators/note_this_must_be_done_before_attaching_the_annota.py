import numpy as np
from isaacsim.sensors.rtx import LidarRtx

# Set the auxOutputType to BASIC (or higher) to enable emitterId output
kwargs = {
    "omni:sensor:Core:auxOutputType": "BASIC",
}

sensor = LidarRtx(
    prim_path="/lidar",
    translation=np.array([0.0, 0.0, 1.0]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
    config_file_name="Example_Rotary",
    **kwargs,
)

sensor.initialize()
# Initialize the specified Annotator with the flags as keyword arguments, then attach it to the render product.
sensor.attach_annotator("IsaacCreateRTXLidarScanBuffer", outputTimestamp=True, outputEmitterId=True)
