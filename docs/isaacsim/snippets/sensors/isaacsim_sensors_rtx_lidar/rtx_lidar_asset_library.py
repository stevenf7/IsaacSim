import omni
from pxr import Gf

_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/lidar",
    config="picoScan150",
    variant="Profile_11",
)
