from isaacsim.sensors.experimental.rtx import Acoustic

# Render at 10 Hz regardless of simulation frame rate.
acoustic = Acoustic.create("/World/Acoustic", tick_rate=10.0)
