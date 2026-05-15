import omni.kit.commands
from pxr import Gf

omni.kit.commands.execute(
    "IsaacSensorCreateRtxUltrasonic",
    path="/Ultrasonic",
    parent="/World/Robot",
    translation=Gf.Vec3d(0.0, 0.0, 0.0),
)
