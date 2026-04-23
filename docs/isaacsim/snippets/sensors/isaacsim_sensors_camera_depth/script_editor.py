from isaacsim.sensors.experimental.rtx import RtxCamera, SingleViewDepthCameraSensor

# Create a camera and attach the depth sensor
cam = RtxCamera("/World/depth_camera")

# Create a depth sensor with depth annotators
sensor = SingleViewDepthCameraSensor(
    cam,
    resolution=(720, 1280),
    annotators=["depth_sensor_distance"],
)
sensor.set_enabled_post_processing(True)

# Configure depth sensor parameters
sensor.set_sensor_baseline(55.0)
sensor.set_sensor_focal_length(897.0)
sensor.set_sensor_distance_cutoffs(minimum_distance=0.5, maximum_distance=100.0)
