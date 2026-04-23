from isaacsim.sensors.experimental.rtx import RtxCamera, SingleViewDepthCameraSensor

cam = RtxCamera("/World/depth_sensor")
sensor = SingleViewDepthCameraSensor(cam, resolution=(720, 1280), annotators=["depth_sensor_distance"])
sensor.set_enabled_post_processing(True)
