# -- Test setup --
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.storage.native import get_assets_root_path

asset_path = get_assets_root_path() + "/Isaac/Robots/IsaacSim/SimpleArticulation/simple_articulation.usd"
stage_utils.add_reference_to_stage(asset_path, path="/World/simple_articulation")
# -- End test setup --
# [create-sensor]
import numpy as np
from isaacsim.sensors.experimental.physics import EffortSensor

sensor = EffortSensor(prim_path="/World/simple_articulation/Arm/RevoluteJoint", enabled=True)
# [/create-sensor]

# [read-sensor]
reading = sensor.get_sensor_reading()
# [/read-sensor]
