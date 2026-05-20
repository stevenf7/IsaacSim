from isaacsim.sensors.experimental.rtx import Lidar

# Render the Lidar at 10 Hz independently of the simulation frame rate.
lidar = Lidar(path="/World/Lidar", tick_rate=10.0)
