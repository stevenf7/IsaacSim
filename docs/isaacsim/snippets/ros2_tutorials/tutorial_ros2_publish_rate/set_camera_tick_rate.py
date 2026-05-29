# Test setup: the tutorial scene already contains these cameras;
# create them here so the snippet can runs on the empty snippet-test stage.
import omni.usd
from pxr import UsdGeom

_stage = omni.usd.get_context().get_stage()
for _path in ("/World/Camera_1", "/World/Camera_2"):
    UsdGeom.Camera.Define(_stage, _path)
# End test setup

import isaacsim.core.experimental.utils.prim as prim_utils

# Cameras created from the Create > Camera menu lack the OmniSensorAPI schema,
# so omni:sensor:tickRate is unavailable until the schema is applied. Apply it to
# each existing camera, then set the publish rate (Hz).
for path in ("/World/Camera_1", "/World/Camera_2"):
    camera_prim = prim_utils.get_prim_at_path(path)
    camera_prim.ApplyAPI("OmniSensorAPI")
    camera_prim.GetAttribute("omni:sensor:tickRate").Set(15)
