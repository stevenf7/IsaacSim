import numpy as np
import omni
from isaacsim.sensors.rtx import LidarRtx

sensor = LidarRtx(
    prim_path="/lidar",
    translation=np.array([0.0, 0.0, 1.0]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
    config_file_name="Example_Rotary",
)
sensor.initialize()
# Initialize the specified Annotator with the flags as keyword arguments, then attach it to the render product.
sensor.attach_annotator("IsaacCreateRTXLidarScanBuffer", outputTimestamp=True, outputMaterialId=True)
