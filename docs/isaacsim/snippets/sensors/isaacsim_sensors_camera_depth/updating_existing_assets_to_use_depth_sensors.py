import os

from isaacsim.sensors.experimental.rtx import RtxCamera, SingleViewDepthCameraSensor

usd_path = os.path.join(
    os.getcwd(),
    "_example_output_isaacsim.sensors.experimental.rtx",
    "create_camera_depth_sensor",
    "example_camera_with_depth_sensor.usd",
)

cam = RtxCamera.create("/World/depth_sensor", usd_path=usd_path)
sensor = SingleViewDepthCameraSensor(cam, resolution=(720, 1280), annotators=["depth_sensor_distance"])
sensor.set_enabled_post_processing(True)
