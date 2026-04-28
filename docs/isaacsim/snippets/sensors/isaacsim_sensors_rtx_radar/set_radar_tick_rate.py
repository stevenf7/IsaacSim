import carb
from isaacsim.sensors.experimental.rtx import Radar

# RTX Radar requires Motion BVH to be enabled.
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")

# Render at 10 Hz regardless of simulation frame rate.
radar = Radar(path="/Radar", tick_rate=10.0)
