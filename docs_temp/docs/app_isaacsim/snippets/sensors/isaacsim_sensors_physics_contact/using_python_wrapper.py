import numpy as np
from isaacsim.sensors.experimental.physics import ContactSensor

sensor = ContactSensor(
    prim_path="/World/Cube/Contact_Sensor",
    name="Contact_Sensor",
    translation=np.array([0, 0, 0]),
    min_threshold=0,
    max_threshold=10000000,
    radius=-1,
)
