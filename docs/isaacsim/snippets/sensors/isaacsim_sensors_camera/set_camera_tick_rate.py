from isaacsim.sensors.experimental.rtx import RtxCamera

# Render the Camera at 30 Hz independently of the simulation frame rate.
camera = RtxCamera(path="/World/Camera", tick_rate=30.0)
