import omni
from pxr import Gf

# Specify attributes to apply to the ``OmniLidar`` prim.
sensor_attributes = {"omni:sensor:Core:scanRateBaseHz": 20}

_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    translation=Gf.Vec3d(0, 0, 0),
    orientation=Gf.Quatd(
        1,
        0,
        0,
        0,
    ),
    path="/lidar",
    parent=None,
    config="Example_Rotary",
    visibility=False,
    variant=None,
    force_camera_prim=False,
    **sensor_attributes,
)
