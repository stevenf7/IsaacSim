from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera

sensor = CameraSensor(
    RtxCamera(
        "/World/Camera",
        tick_rate=30.0,
        translations=[[0.0, 0.0, 1.0]],
    ),
    resolution=(640, 480),
    annotators=["rgb"],
)
data, info = sensor.get_data("rgb")
