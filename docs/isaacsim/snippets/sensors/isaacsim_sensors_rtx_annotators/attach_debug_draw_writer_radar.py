import carb
import numpy as np
import omni.kit.app
import omni.replicator.core as rep
from isaacsim.sensors.experimental.rtx import Radar

# RTX Radar requires Motion BVH to be enabled.
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")

# The debug draw writer is registered by isaacsim.sensors.rtx.nodes.
omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("isaacsim.sensors.rtx.nodes", True)

radar = Radar(path="/Radar", tick_rate=20, translations=np.array([0, 0, 1.0]))
render_product = rep.create.render_product(radar.paths[0], resolution=(1, 1))

writer = rep.writers.get("RtxSensorDebugDrawPointCloud")
writer.initialize(size=0.2, color=[1.0, 0.3, 0.1, 1.0])  # orange, larger points
writer.attach([render_product.path])
