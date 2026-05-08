import carb
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.sensors.experimental.rtx import Radar

# RTX Radar requires Motion BVH to be enabled for Doppler velocity estimation.
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")

# Ensure a /World Xform exists on the stage as the parent for the radar.
stage_utils.define_prim("/World", "Xform")

# Create an RTX Radar with a custom tick rate.
radar = Radar(
    path="/World/radar",
    tick_rate=10,
    translations=np.array([0.0, 0.0, 0.0]),
    orientations=np.array([1.0, 0.0, 0.0, 0.0]),
)
