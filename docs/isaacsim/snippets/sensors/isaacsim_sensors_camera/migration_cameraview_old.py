from isaacsim.sensors.camera import Camera, CameraView

# CameraView wraps existing camera prims, so author them first.
Camera(prim_path="/World/env_0/Camera", position=[0.0, 0.0, 5.0])
Camera(prim_path="/World/env_1/Camera", position=[2.0, 0.0, 5.0])

view = CameraView(
    prim_paths_expr="/World/env_*/Camera",
    camera_resolution=(256, 256),
    output_annotators=["rgb"],
)
