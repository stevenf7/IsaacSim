from isaacsim.sensors.experimental.rtx import Lidar

lidar = Lidar.create(
    path="/World/lidar",
    config="picoScan150",
    variant="Profile_11",
)
