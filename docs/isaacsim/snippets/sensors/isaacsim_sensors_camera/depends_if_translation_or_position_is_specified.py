from isaacsim.sensors.experimental.rtx import RtxCamera

# Create a camera prim with the OmniSensorAPI schema
cam = RtxCamera(
    "/World/camera",
    # translations = ...
    # orientations = ...
)
