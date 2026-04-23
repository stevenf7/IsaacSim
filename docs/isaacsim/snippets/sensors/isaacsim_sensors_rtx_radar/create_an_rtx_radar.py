import carb
import numpy as np
from isaacsim.sensors.experimental.rtx import Radar

# RTX Radar requires Motion BVH to be enabled for Doppler velocity estimation.
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")

# Create an RTX Radar with a custom tick rate.
radar = Radar(
    path="/World/radar",
    tick_rate=10,
    translations=np.array([0.0, 0.0, 0.0]),
    orientations=np.array([1.0, 0.0, 0.0, 0.0]),
)
