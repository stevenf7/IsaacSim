import carb
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

# RTX Radar requires Motion BVH to be enabled.
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")

sensor = RadarSensor(
    Radar.create(
        "/World/Radar",
        translations=[[0.0, 0.0, 0.0]],
    ),
    annotators=["generic-model-output"],
)
data, info = sensor.get_data("generic-model-output")
