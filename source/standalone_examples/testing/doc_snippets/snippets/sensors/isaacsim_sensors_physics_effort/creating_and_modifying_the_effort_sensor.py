import numpy as np
from isaacsim.sensors.physics import EffortSensor

sensor = EffortSensor(
    prim_path="/World/simple_articulation/Arm/RevoluteJoint", sensor_period=0.1, use_latest_data=False, enabled=True
)
