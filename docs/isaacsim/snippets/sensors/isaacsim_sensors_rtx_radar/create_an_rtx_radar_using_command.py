import omni
from pxr import Gf

# Specify attributes to apply to the ``OmniRadar`` prim.
sensor_attributes = {"omni:sensor:tickRate": 10}

_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxRadar",
    translation=Gf.Vec3d(0, 0, 0),
    orientation=Gf.Quatd(1, 0, 0, 0),
    path="/radar",
    parent=None,
    visibility=False,
    variant=None,
    force_camera_prim=False,
    **sensor_attributes,
)
