import omni.kit.commands
from pxr import Gf

success, _isaac_sensor_prim = omni.kit.commands.execute(
    "IsaacSensorCreateContactSensor",
    path="Contact_Sensor",
    parent="/World/Cube",
    sensor_period=1,
    min_threshold=0.0001,
    max_threshold=100000,
    translation=Gf.Vec3d(0, 0, 0),
)
