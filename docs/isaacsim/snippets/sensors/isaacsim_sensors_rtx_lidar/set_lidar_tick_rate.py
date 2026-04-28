from isaacsim.sensors.experimental.rtx import Lidar

# Render at 10 Hz regardless of simulation frame rate.
lidar = Lidar.create("/World/Lidar", config="Example_Rotary", tick_rate=10.0)
