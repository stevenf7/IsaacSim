import omni.kit.commands
from pxr import Gf

omni.kit.commands.execute(
    "IsaacSensorCreateRtxRadar",
    path="/Radar",
    parent="/World/Robot",
    config="Example_Radar",
    translation=Gf.Vec3d(0.0, 0.0, 0.0),
)
