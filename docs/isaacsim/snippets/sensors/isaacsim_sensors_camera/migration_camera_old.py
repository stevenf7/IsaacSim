from isaacsim.sensors.camera import Camera

camera = Camera(
    prim_path="/World/Camera",
    resolution=(640, 480),
    frequency=30,
    position=[0.0, 0.0, 1.0],
)
camera.initialize()
camera.add_rgb_to_frame()
frame = camera.get_current_frame()
