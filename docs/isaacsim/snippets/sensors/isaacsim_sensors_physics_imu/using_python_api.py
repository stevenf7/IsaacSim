from isaacsim.sensors.experimental.physics import IMUSensor
from pxr import Gf

sensor = IMUSensor.create(
    "/World/Cube/imu_sensor",
    linear_acceleration_filter_size=10,
    angular_velocity_filter_size=10,
    orientation_filter_size=10,
    translation=Gf.Vec3d(0, 0, 0),
    orientation=Gf.Quatd(1, 0, 0, 0),
)
