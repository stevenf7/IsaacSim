import numpy as np
from isaacsim.sensors.physics import ContactSensor

sensor = ContactSensor(
    prim_path="/World/Cube/Contact_Sensor",
    name="Contact_Sensor",
    frequency=60,
    translation=np.array([0, 0, 0]),
    min_threshold=0,
    max_threshold=10000000,
    radius=-1,
)

value = sensor.get_current_frame()
print(value)
