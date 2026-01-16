import omni.kit.commands
from pxr import Gf

success, _isaac_sensor_prim = omni.kit.commands.execute(
    "IsaacSensorCreateImuSensor",
    path="imu_sensor",
    parent="/World/Cube",
    sensor_period=1,
    linear_acceleration_filter_size=10,
    angular_velocity_filter_size=10,
    orientation_filter_size=10,
    translation=Gf.Vec3d(0, 0, 0),
    orientation=Gf.Quatd(1, 0, 0, 0),
)
