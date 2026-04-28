import carb
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor, parse_generic_model_output_data

# RTX Radar requires Motion BVH to be enabled.
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")

radar = Radar(path="/Radar")

sensor = RadarSensor(radar, annotators=["generic-model-output"])
data, info = sensor.get_data("generic-model-output")
