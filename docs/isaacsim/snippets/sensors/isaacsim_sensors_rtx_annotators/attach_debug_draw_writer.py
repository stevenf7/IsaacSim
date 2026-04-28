import omni.kit.app
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor

# The "draw-point-cloud" writer is registered by isaacsim.sensors.rtx.nodes.
# Make sure that extension is enabled before constructing the sensor.
omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("isaacsim.sensors.rtx.nodes", True)

# Create the underlying lidar prim that the sensor will wrap.
Lidar.create("/World/lidar", config="Example_Rotary")

sensor = LidarSensor("/World/lidar", annotators=[], writers=["draw-point-cloud"])
