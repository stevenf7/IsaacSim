from isaacsim.sensors.experimental.physics import ContactSensor
from pxr import Gf

sensor = ContactSensor.create(
    "/World/Cube/Contact_Sensor",
    min_threshold=0.0001,
    max_threshold=100000,
    translation=Gf.Vec3d(0, 0, 0),
)
