import omni

stage = omni.usd.get_context().get_stage()  # Used to access Geometry
timeline = omni.timeline.get_timeline_interface()  # Used to interact with simulation
lidarInterface = _range_sensor.acquire_lidar_sensor_interface()  # Used to interact with the LIDAR

# These commands are the Python-equivalent of the first half of this tutorial
omni.kit.commands.execute("AddPhysicsSceneCommand", stage=stage, path="/World/PhysicsScene")
lidarPath = "/LidarName"
result, prim = omni.kit.commands.execute(
    "RangeSensorCreateLidar",
    path=lidarPath,
    parent="/World",
    min_range=0.4,
    max_range=100.0,
    draw_points=False,
    draw_lines=True,
    horizontal_fov=360.0,
    vertical_fov=30.0,
    horizontal_resolution=0.4,
    vertical_resolution=4.0,
    rotation_rate=0.0,
    high_lod=False,
    yaw_offset=0.0,
    enable_semantics=False,
)
