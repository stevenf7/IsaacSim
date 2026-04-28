from isaacsim.sensors.experimental.rtx import Lidar

# Disable accumulation to get per-frame partial scans.
lidar = Lidar.create("/World/Lidar", config="Example_Rotary", accumulate_outputs=False)
